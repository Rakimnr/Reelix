package com.reelix.reelix

import android.animation.ObjectAnimator
import android.animation.PropertyValuesHolder
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.graphics.Color
import android.graphics.PixelFormat
import android.hardware.display.DisplayManager
import android.hardware.display.VirtualDisplay
import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioPlaybackCaptureConfiguration
import android.media.AudioRecord
import android.media.ImageReader
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.util.Log
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.FrameLayout
import android.widget.ProgressBar
import android.widget.TextView
import androidx.core.app.NotificationCompat
import java.io.File
import kotlin.concurrent.thread

class ScannerService : Service() {
    companion object {
        const val TAG = "ReelixScanner"
        const val ACTION_START = "ACTION_START"
        const val ACTION_STOP = "ACTION_STOP"
        const val ACTION_START_PROJECTION = "ACTION_START_PROJECTION"
        const val EXTRA_RESULT_CODE = "EXTRA_RESULT_CODE"
        const val EXTRA_RESULT_DATA = "EXTRA_RESULT_DATA"
        const val NOTIFICATION_ID = 101
        const val CHANNEL_ID = "ReelixScannerChannel"
    }

    private var windowManager: WindowManager? = null
    private var bubbleView: View? = null
    private var removeTargetView: View? = null
    private var bubbleParams: WindowManager.LayoutParams? = null
    
    private var mediaProjection: MediaProjection? = null
    private var virtualDisplay: VirtualDisplay? = null
    private var imageReader: ImageReader? = null
    private var audioRecord: AudioRecord? = null
    
    private var isCapturing = false
    private var backendUrl: String = "http://10.0.2.2:8000"
    
    @Volatile private var latestFrameBytes: ByteArray? = null
    @Volatile private var latestFrameWidth = 0
    @Volatile private var latestFrameHeight = 0
    private val frameLock = Object()
    
    private var capturedFramePaths = mutableListOf<String>()
    @Volatile private var capturedAudioPath: String? = null

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START -> {
                Log.d(TAG, "[Reelix][SCANNER_STATE] Starting service")
                intent.getStringExtra("backend_url")?.let {
                    backendUrl = it
                }
                showBubble()
            }
            ACTION_START_PROJECTION -> {
                val resultCode = intent.getIntExtra(EXTRA_RESULT_CODE, 0)
                val resultData = intent.getParcelableExtra<Intent>(EXTRA_RESULT_DATA)
                if (resultCode != 0 && resultData != null) {
                    Log.d(TAG, "[Reelix][PROJECTION] session_started")
                    
                    createNotificationChannel()
                    val notification = NotificationCompat.Builder(this, CHANNEL_ID)
                        .setContentTitle("Reelix Scanner Active")
                        .setContentText("Capturing...")
                        .setSmallIcon(android.R.drawable.ic_menu_camera)
                        .build()
                        
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                        startForeground(NOTIFICATION_ID, notification, android.content.pm.ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION)
                    } else {
                        startForeground(NOTIFICATION_ID, notification)
                    }
                    
                    setupMediaProjection(resultCode, resultData)
                    runCaptureAndUpload()
                } else {
                    setBubbleState("ERROR")
                }
            }
            ACTION_STOP -> {
                Log.d(TAG, "[Reelix][SCANNER_STATE] Stopping service")
                stopScanner()
                stopSelf()
            }
        }
        return START_NOT_STICKY
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Reelix Scanner Service",
                NotificationManager.IMPORTANCE_LOW
            )
            val manager = getSystemService(NotificationManager::class.java)
            manager?.createNotificationChannel(channel)
        }
    }

    private fun showBubble() {
        if (bubbleView != null) return
        
        windowManager = getSystemService(WINDOW_SERVICE) as WindowManager
        
        // Remove Target View (Bottom Center)
        val removeParams = WindowManager.LayoutParams(
            200, 200,
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY else WindowManager.LayoutParams.TYPE_PHONE,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
            PixelFormat.TRANSLUCENT
        )
        removeParams.gravity = Gravity.BOTTOM or Gravity.CENTER_HORIZONTAL
        removeParams.y = 100
        
        val removeLayout = FrameLayout(this)
        removeLayout.setBackgroundColor(Color.parseColor("#88FF0000"))
        val removeText = TextView(this).apply {
            text = "✖"
            textSize = 30f
            gravity = Gravity.CENTER
            setTextColor(Color.WHITE)
        }
        removeLayout.addView(removeText)
        removeLayout.visibility = View.GONE
        removeTargetView = removeLayout
        windowManager?.addView(removeTargetView, removeParams)
        
        // Main Bubble View
        bubbleParams = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY else WindowManager.LayoutParams.TYPE_PHONE,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
            PixelFormat.TRANSLUCENT
        )
        bubbleParams?.gravity = Gravity.TOP or Gravity.START
        bubbleParams?.x = 0
        bubbleParams?.y = 300

        val bubbleLayout = FrameLayout(this)
        bubbleLayout.setPadding(20, 20, 20, 20)
        bubbleLayout.setBackgroundColor(0x88000000.toInt())
        
        val progressBar = ProgressBar(this).apply {
            visibility = View.GONE
        }
        val iconText = TextView(this).apply {
            text = "🎥"
            textSize = 30f
            gravity = Gravity.CENTER
        }
        bubbleLayout.addView(progressBar)
        bubbleLayout.addView(iconText)
        bubbleView = bubbleLayout
        
        var initialX = 0
        var initialY = 0
        var initialTouchX = 0f
        var initialTouchY = 0f
        var isDragging = false
        
        bubbleView?.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    initialX = bubbleParams!!.x
                    initialY = bubbleParams!!.y
                    initialTouchX = event.rawX
                    initialTouchY = event.rawY
                    isDragging = false
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val xDiff = Math.abs(event.rawX - initialTouchX)
                    val yDiff = Math.abs(event.rawY - initialTouchY)
                    if (xDiff > 10 || yDiff > 10) {
                        if (!isDragging) {
                            isDragging = true
                            Log.d(TAG, "[Reelix][BUBBLE] drag_started")
                            removeTargetView?.visibility = View.VISIBLE
                            Log.d(TAG, "[Reelix][BUBBLE] remove_target_shown")
                        }
                        
                        bubbleParams!!.x = initialX + (event.rawX - initialTouchX).toInt()
                        bubbleParams!!.y = initialY + (event.rawY - initialTouchY).toInt()
                        windowManager?.updateViewLayout(bubbleView, bubbleParams)
                        
                        // Highlight target if close
                        val metrics = resources.displayMetrics
                        val screenHeight = metrics.heightPixels
                        if (event.rawY > screenHeight - 400) {
                            removeTargetView?.scaleX = 1.2f
                            removeTargetView?.scaleY = 1.2f
                        } else {
                            removeTargetView?.scaleX = 1.0f
                            removeTargetView?.scaleY = 1.0f
                        }
                    }
                    true
                }
                MotionEvent.ACTION_UP -> {
                    if (isDragging) {
                        removeTargetView?.visibility = View.GONE
                        val metrics = resources.displayMetrics
                        val screenHeight = metrics.heightPixels
                        if (event.rawY > screenHeight - 400) {
                            Log.d(TAG, "[Reelix][BUBBLE] removed")
                            stopScanner()
                            stopSelf()
                        }
                    } else {
                        // Tapped
                        if (!isCapturing) {
                            onBubbleTapped()
                        }
                    }
                    true
                }
                else -> false
            }
        }
        
        windowManager?.addView(bubbleView, bubbleParams)
        Log.d(TAG, "[Reelix][OVERLAY] bubble shown")
        setBubbleState("IDLE")
    }
    
    private fun setBubbleState(state: String) {
        Handler(Looper.getMainLooper()).post {
            Log.d(TAG, "[Reelix][BUBBLE_STATE] $state")
            val layout = bubbleView as? FrameLayout ?: return@post
            val progressBar = layout.getChildAt(0) as ProgressBar
            val iconText = layout.getChildAt(1) as TextView
            
            progressBar.visibility = View.GONE
            iconText.visibility = View.VISIBLE
            iconText.clearAnimation()
            
            when (state) {
                "IDLE" -> {
                    iconText.text = "🎥"
                }
                "CAPTURING" -> {
                    iconText.text = "🎥"
                    val pulse = ObjectAnimator.ofPropertyValuesHolder(
                        iconText,
                        PropertyValuesHolder.ofFloat("scaleX", 1.2f),
                        PropertyValuesHolder.ofFloat("scaleY", 1.2f)
                    )
                    pulse.duration = 300
                    pulse.repeatCount = ObjectAnimator.INFINITE
                    pulse.repeatMode = ObjectAnimator.REVERSE
                    pulse.start()
                }
                "ANALYZING" -> {
                    iconText.visibility = View.GONE
                    progressBar.visibility = View.VISIBLE
                }
                "SUCCESS" -> {
                    iconText.text = "✅"
                }
                "ERROR" -> {
                    iconText.text = "❌"
                }
            }
        }
    }

    private fun onBubbleTapped() {
        if (isCapturing) return
        isCapturing = true
        setBubbleState("CAPTURING")

        val intent = Intent(this, CaptureConsentActivity::class.java)
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        startActivity(intent)
    }

    private fun setupMediaProjection(resultCode: Int, data: Intent) {
        synchronized(frameLock) {
            latestFrameBytes = null
        }
        val projectionManager = getSystemService(Context.MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
        mediaProjection = projectionManager.getMediaProjection(resultCode, data)
        mediaProjection?.registerCallback(object : MediaProjection.Callback() {
            override fun onStop() {
                // Ignore since we handle stopping manually per-scan now
            }
        }, null)
        createVirtualDisplay()
    }

    private fun createVirtualDisplay() {
        val metrics = resources.displayMetrics
        val width = metrics.widthPixels
        val height = metrics.heightPixels
        val density = metrics.densityDpi

        imageReader = ImageReader.newInstance(width, height, PixelFormat.RGBA_8888, 2)
        imageReader?.setOnImageAvailableListener({ reader ->
            try {
                val image = reader.acquireLatestImage()
                if (image != null) {
                    try {
                        val planes = image.planes
                        val buffer = planes[0].buffer
                        val pixelStride = planes[0].pixelStride
                        val rowStride = planes[0].rowStride
                        
                        val bytes = ByteArray(buffer.remaining())
                        buffer.get(bytes)
                        
                        synchronized(frameLock) {
                            latestFrameBytes = bytes
                            latestFrameWidth = width
                            latestFrameHeight = height
                        }
                    } finally {
                        image.close()
                    }
                }
            } catch (e: Exception) { }
        }, Handler(Looper.getMainLooper()))
        
        virtualDisplay = mediaProjection?.createVirtualDisplay(
            "ReelixCapture",
            width, height, density,
            DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
            imageReader?.surface, null, null
        )
    }
    
    private fun runCaptureAndUpload() {
        thread {
            capturedAudioPath = null
            val audioThread = thread {
                captureAudio()
            }
            
            captureVisualBurst(targetFrames = 5, durationMs = 2000L)
            audioThread.join() // strictly wait for memory visibility and thread completion
            
            setBubbleState("ANALYZING")
            
            Log.d(TAG, "[Reelix][UPLOAD] evidence ready")
            val hasAudio = capturedAudioPath != null
            Log.d(TAG, "[Reelix][UPLOAD] frames=${capturedFramePaths.size} audio=${if(hasAudio) "yes" else "no"}")
            Log.d(TAG, "[Reelix][UPLOAD] backend=$backendUrl")
            
            val urlString = "$backendUrl/recognize"
            var jsonResponse: String? = null
            var success = false
            
            try {
                Log.d(TAG, "[Reelix][UPLOAD] request started")
                val url = java.net.URL(urlString)
                val connection = url.openConnection() as java.net.HttpURLConnection
                val boundary = "*****" + System.currentTimeMillis() + "*****"
                val twoHyphens = "--"
                val crlf = "\r\n"
                
                connection.requestMethod = "POST"
                connection.setRequestProperty("Connection", "Keep-Alive")
                connection.setRequestProperty("Cache-Control", "no-cache")
                connection.setRequestProperty("Content-Type", "multipart/form-data;boundary=$boundary")
                connection.doOutput = true
                connection.doInput = true
                
                val out = java.io.DataOutputStream(connection.outputStream)
                
                // Write frames
                for (framePath in capturedFramePaths) {
                    val file = File(framePath)
                    out.writeBytes(twoHyphens + boundary + crlf)
                    out.writeBytes("Content-Disposition: form-data; name=\"frames\";filename=\"${file.name}\"" + crlf)
                    out.writeBytes("Content-Type: image/jpeg" + crlf)
                    out.writeBytes(crlf)
                    
                    val fileInput = java.io.FileInputStream(file)
                    fileInput.copyTo(out)
                    fileInput.close()
                    out.writeBytes(crlf)
                }
                
                // Write audio
                if (capturedAudioPath != null) {
                    val file = File(capturedAudioPath!!)
                    out.writeBytes(twoHyphens + boundary + crlf)
                    out.writeBytes("Content-Disposition: form-data; name=\"audio\";filename=\"${file.name}\"" + crlf)
                    out.writeBytes("Content-Type: audio/wav" + crlf)
                    out.writeBytes(crlf)
                    
                    val fileInput = java.io.FileInputStream(file)
                    fileInput.copyTo(out)
                    fileInput.close()
                    out.writeBytes(crlf)
                }
                
                out.writeBytes(twoHyphens + boundary + twoHyphens + crlf)
                out.flush()
                out.close()
                
                val responseCode = connection.responseCode
                Log.d(TAG, "[Reelix][UPLOAD] response status=$responseCode")
                
                val ins = if (responseCode in 200..299) connection.inputStream else connection.errorStream
                if (ins != null) {
                    jsonResponse = ins.bufferedReader().use { it.readText() }
                    Log.d(TAG, "[Reelix][UPLOAD] response body=$jsonResponse")
                    if (responseCode in 200..299) success = true
                }
                
            } catch (e: Exception) {
                Log.d(TAG, "[Reelix][UPLOAD] error=${e.message}")
            }
            
            Handler(Looper.getMainLooper()).post {
                if (success) {
                    setBubbleState("SUCCESS")
                    if (jsonResponse != null) {
                        val intent = Intent("com.reelix.SCAN_RESULT")
                        intent.putExtra("result_json", jsonResponse)
                        sendBroadcast(intent)
                    }
                } else {
                    setBubbleState("ERROR")
                }
                
                // Clean up per-scan media projection session
                releaseProjectionSession()
                
                // Clean up evidence files
                cleanupTempData()
                
                // Wait briefly before resetting state
                Handler(Looper.getMainLooper()).postDelayed({
                    setBubbleState("IDLE")
                    isCapturing = false
                }, 1500)
            }
        }
    }

    private fun releaseProjectionSession() {
        virtualDisplay?.release()
        virtualDisplay = null
        imageReader?.close()
        imageReader = null
        mediaProjection?.stop()
        mediaProjection = null
        stopForeground(true)
        Log.d(TAG, "[Reelix][PROJECTION] session_released")
    }

    private fun getFileHash(file: File): String {
        try {
            val md = java.security.MessageDigest.getInstance("MD5")
            val bytes = file.readBytes()
            val digest = md.digest(bytes)
            return digest.joinToString("") { "%02x".format(it) }.take(8)
        } catch (e: Exception) {
            return "error"
        }
    }

    private fun captureVisualBurst(targetFrames: Int, durationMs: Long) {
        capturedFramePaths.clear()
        
        Log.d(TAG, "[Reelix][VISUAL_CAPTURE] waiting_for_first_frame")
        val warmupStart = System.currentTimeMillis()
        var hasFirstFrame = false
        
        while (System.currentTimeMillis() - warmupStart < 1500) {
            synchronized(frameLock) {
                if (latestFrameBytes != null) {
                    hasFirstFrame = true
                }
            }
            if (hasFirstFrame) break
            Thread.sleep(50)
        }
        
        if (hasFirstFrame) {
            Log.d(TAG, "[Reelix][VISUAL_CAPTURE] first_frame_ready")
        } else {
            Log.d(TAG, "[Reelix][VISUAL_CAPTURE] timeout frames=0")
            Log.d(TAG, "[Reelix][VISUAL_CAPTURE] frames_saved=0 unique_hashes=0")
            return
        }

        val intervalMs = durationMs / targetFrames
        val hashSet = mutableSetOf<String>()
        
        for (i in 0 until targetFrames) {
            val sampleStartTime = System.currentTimeMillis()
            var frameCopy: ByteArray? = null
            var width = 0
            var height = 0
            
            synchronized(frameLock) {
                if (latestFrameBytes != null) {
                    frameCopy = latestFrameBytes!!.clone()
                    width = latestFrameWidth
                    height = latestFrameHeight
                }
            }
            
            if (frameCopy != null) {
                try {
                    val bitmap = android.graphics.Bitmap.createBitmap(width, height, android.graphics.Bitmap.Config.ARGB_8888)
                    bitmap.copyPixelsFromBuffer(java.nio.ByteBuffer.wrap(frameCopy!!))
                    
                    val file = File(cacheDir, "reelix_temp_frame_${System.currentTimeMillis()}_$i.jpg")
                    val out = java.io.FileOutputStream(file)
                    bitmap.compress(android.graphics.Bitmap.CompressFormat.JPEG, 80, out)
                    out.flush()
                    out.close()
                    
                    val hash = getFileHash(file)
                    hashSet.add(hash)
                    Log.d(TAG, "[Reelix][VISUAL_CAPTURE] frame=${i + 1} timestamp=${System.currentTimeMillis()} hash=$hash")
                    
                    capturedFramePaths.add(file.absolutePath)
                } catch(e: Exception) {
                    Log.e(TAG, "Error saving JPEG", e)
                }
            }
            
            val elapsed = System.currentTimeMillis() - sampleStartTime
            val waitTime = intervalMs - elapsed
            if (waitTime > 0) Thread.sleep(waitTime)
        }
        
        if (capturedFramePaths.size < targetFrames) {
            Log.d(TAG, "[Reelix][VISUAL_CAPTURE] timeout frames=${capturedFramePaths.size}")
        }
        Log.d(TAG, "[Reelix][VISUAL_CAPTURE] frames_saved=${capturedFramePaths.size} unique_hashes=${hashSet.size}")
    }

    private fun saveWavFile(shortData: ShortArray, sampleRate: Int, numSamples: Int): String? {
        try {
            val file = File(cacheDir, "reelix_temp_audio_${System.currentTimeMillis()}.wav")
            val out = java.io.FileOutputStream(file)
            val byteRate = sampleRate * 2
            val totalDataLen = numSamples * 2
            val totalAudioLen = totalDataLen + 36
            
            val header = ByteArray(44)
            header[0] = 'R'.code.toByte(); header[1] = 'I'.code.toByte(); header[2] = 'F'.code.toByte(); header[3] = 'F'.code.toByte()
            header[4] = (totalAudioLen and 0xff).toByte(); header[5] = ((totalAudioLen shr 8) and 0xff).toByte(); header[6] = ((totalAudioLen shr 16) and 0xff).toByte(); header[7] = ((totalAudioLen shr 24) and 0xff).toByte()
            header[8] = 'W'.code.toByte(); header[9] = 'A'.code.toByte(); header[10] = 'V'.code.toByte(); header[11] = 'E'.code.toByte()
            header[12] = 'f'.code.toByte(); header[13] = 'm'.code.toByte(); header[14] = 't'.code.toByte(); header[15] = ' '.code.toByte()
            header[16] = 16; header[17] = 0; header[18] = 0; header[19] = 0
            header[20] = 1; header[21] = 0
            header[22] = 1; header[23] = 0 
            header[24] = (sampleRate and 0xff).toByte(); header[25] = ((sampleRate shr 8) and 0xff).toByte(); header[26] = ((sampleRate shr 16) and 0xff).toByte(); header[27] = ((sampleRate shr 24) and 0xff).toByte()
            header[28] = (byteRate and 0xff).toByte(); header[29] = ((byteRate shr 8) and 0xff).toByte(); header[30] = ((byteRate shr 16) and 0xff).toByte(); header[31] = ((byteRate shr 24) and 0xff).toByte()
            header[32] = 2; header[33] = 0
            header[34] = 16; header[35] = 0
            header[36] = 'd'.code.toByte(); header[37] = 'a'.code.toByte(); header[38] = 't'.code.toByte(); header[39] = 'a'.code.toByte()
            header[40] = (totalDataLen and 0xff).toByte(); header[41] = ((totalDataLen shr 8) and 0xff).toByte(); header[42] = ((totalDataLen shr 16) and 0xff).toByte(); header[43] = ((totalDataLen shr 24) and 0xff).toByte()
            
            out.write(header, 0, 44)
            
            val byteData = ByteArray(totalDataLen)
            for (i in 0 until numSamples) {
                byteData[i*2] = (shortData[i].toInt() and 0xff).toByte()
                byteData[i*2+1] = ((shortData[i].toInt() shr 8) and 0xff).toByte()
            }
            out.write(byteData)
            out.close()
            return file.absolutePath
        } catch(e: Exception) {
            return null
        }
    }

    private fun captureAudio() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            val sampleRate = 22050
            val channelConfig = AudioFormat.CHANNEL_IN_MONO
            val audioFormat = AudioFormat.ENCODING_PCM_16BIT
            val minBufferSize = AudioRecord.getMinBufferSize(sampleRate, channelConfig, audioFormat)
            
            val config = AudioPlaybackCaptureConfiguration.Builder(mediaProjection!!)
                .addMatchingUsage(AudioAttributes.USAGE_MEDIA)
                .addMatchingUsage(AudioAttributes.USAGE_GAME)
                .addMatchingUsage(AudioAttributes.USAGE_UNKNOWN)
                .build()
                
            try {
                audioRecord = AudioRecord.Builder()
                    .setAudioFormat(
                        AudioFormat.Builder()
                            .setEncoding(audioFormat)
                            .setSampleRate(sampleRate)
                            .setChannelMask(channelConfig)
                            .build()
                    )
                    .setAudioPlaybackCaptureConfig(config)
                    .setBufferSizeInBytes(minBufferSize * 2)
                    .build()
                    
                val durationMs = 6000L
                Log.d(TAG, "[Reelix][AUDIO_CAPTURE] target_duration=${durationMs / 1000.0}s")
                
                audioRecord?.startRecording()
                
                val maxSamples = (sampleRate * (durationMs / 1000.0)).toInt()
                val buffer = ShortArray(maxSamples)
                
                var totalSamples = 0
                val startTime = System.currentTimeMillis()
                var isSilent = true
                
                while (System.currentTimeMillis() - startTime < durationMs && totalSamples < maxSamples) {
                    val readSize = Math.min(minBufferSize, maxSamples - totalSamples)
                    val read = audioRecord?.read(buffer, totalSamples, readSize, AudioRecord.READ_NON_BLOCKING) ?: 0
                    if (read > 0) {
                        for (i in 0 until read) {
                            if (buffer[totalSamples + i] != 0.toShort()) {
                                isSilent = false
                            }
                        }
                        totalSamples += read
                    }
                }
                
                audioRecord?.stop()
                audioRecord?.release()
                audioRecord = null
                
                val durationS = durationMs / 1000.0
                if (isSilent && totalSamples > 0) {
                    Log.d(TAG, "[Reelix][AUDIO_CAPTURE] duration=${durationS}s nonSilent=false status=AUDIO_BLOCKED_OR_SILENT")
                    capturedAudioPath = null
                } else if (totalSamples > 0) {
                    Log.d(TAG, "[Reelix][AUDIO_CAPTURE] duration=${durationS}s nonSilent=true status=AUDIO_CAPTURED samples=$totalSamples")
                    capturedAudioPath = saveWavFile(buffer, sampleRate, totalSamples)
                } else {
                    Log.d(TAG, "[Reelix][AUDIO_CAPTURE] status=AUDIO_UNAVAILABLE")
                    capturedAudioPath = null
                }
                
            } catch (e: Exception) {
                Log.d(TAG, "[Reelix][AUDIO_CAPTURE] status=AUDIO_ERROR msg=${e.message}")
                capturedAudioPath = null
            }
        } else {
            Log.d(TAG, "[Reelix][AUDIO_CAPTURE] Not supported below API 29")
            capturedAudioPath = null
        }
    }

    private fun cleanupTempData() {
        try {
            val cacheDir = cacheDir
            val tempFiles = cacheDir.listFiles()
            var deleted = 0
            tempFiles?.forEach {
                if (it.name.startsWith("reelix_temp")) {
                    it.delete()
                    deleted++
                }
            }
            Log.d(TAG, "[Reelix][TEMP_CLEANUP] complete files_deleted=$deleted")
        } catch (e: Exception) {
            Log.e(TAG, "Error in cleanup", e)
        }
    }

    private fun stopScanner() {
        releaseProjectionSession()
        if (bubbleView != null) {
            windowManager?.removeView(bubbleView)
            bubbleView = null
        }
        if (removeTargetView != null) {
            windowManager?.removeView(removeTargetView)
            removeTargetView = null
        }
        stopForeground(true)
    }
}
