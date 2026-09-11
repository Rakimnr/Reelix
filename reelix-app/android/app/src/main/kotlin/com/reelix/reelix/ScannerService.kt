package com.reelix.reelix

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
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
import android.util.DisplayMetrics
import android.util.Log
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.TextView
import androidx.core.app.NotificationCompat
import java.io.File
import kotlin.concurrent.thread

class ScannerService : Service() {

    companion object {
        const val ACTION_START = "ACTION_START"
        const val ACTION_STOP = "ACTION_STOP"
        const val EXTRA_RESULT_CODE = "EXTRA_RESULT_CODE"
        const val EXTRA_RESULT_DATA = "EXTRA_RESULT_DATA"
        private const val NOTIFICATION_ID = 1
        private const val CHANNEL_ID = "ScannerServiceChannel"
        private const val TAG = "ReelixScanner"
    }

    private var mediaProjection: MediaProjection? = null
    private var windowManager: WindowManager? = null
    private var bubbleView: View? = null
    private var virtualDisplay: VirtualDisplay? = null
    private var imageReader: ImageReader? = null
    private var audioRecord: AudioRecord? = null
    
    // State
    private var isCapturing = false

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START -> {
                Log.d(TAG, "[Reelix][SCANNER_STATE] Starting service")
                createNotificationChannel()
                val notification = NotificationCompat.Builder(this, CHANNEL_ID)
                    .setContentTitle("Reelix Scanner Active")
                    .setContentText("Tap the bubble to scan")
                    .setSmallIcon(android.R.drawable.ic_menu_camera)
                    .build()
                startForeground(NOTIFICATION_ID, notification)

                val resultCode = intent.getIntExtra(EXTRA_RESULT_CODE, 0)
                val resultData = intent.getParcelableExtra<Intent>(EXTRA_RESULT_DATA)
                
                if (resultCode != 0 && resultData != null) {
                    setupMediaProjection(resultCode, resultData)
                    showBubble()
                } else {
                    stopSelf()
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

    private fun setupMediaProjection(resultCode: Int, data: Intent) {
        val projectionManager = getSystemService(Context.MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
        mediaProjection = projectionManager.getMediaProjection(resultCode, data)
        Log.d(TAG, "[Reelix][MEDIA_PROJECTION] created")
        
        mediaProjection?.registerCallback(object : MediaProjection.Callback() {
            override fun onStop() {
                Log.d(TAG, "[Reelix][MEDIA_PROJECTION] Callback.onStop() fired")
                stopScanner()
                stopSelf()
            }
        }, null)
        Log.d(TAG, "[Reelix][MEDIA_PROJECTION] started")
        
        createVirtualDisplay()
    }

    private var latestFrameBytes: ByteArray? = null
    private var latestFrameWidth = 0
    private var latestFrameHeight = 0
    private val frameLock = Object()

    private fun createVirtualDisplay() {
        if (virtualDisplay != null) return
        
        val metrics = resources.displayMetrics
        val width = metrics.widthPixels
        val height = metrics.heightPixels
        val density = metrics.densityDpi

        Log.d(TAG, "[Reelix][VISUAL_CAPTURE] ImageReader creating")
        // Max images = 2, we just need to pull and copy continuously
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
                        val rowPadding = rowStride - pixelStride * width
                        
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
            } catch (e: Exception) {
                // Ignore transient errors
            }
        }, Handler(Looper.getMainLooper()))
        
        Log.d(TAG, "[Reelix][VISUAL_CAPTURE] VirtualDisplay creating")
        virtualDisplay = mediaProjection?.createVirtualDisplay(
            "ReelixCapture",
            width, height, density,
            DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
            imageReader?.surface, null, null
        )
    }

    private fun showBubble() {
        if (bubbleView != null) return
        
        windowManager = getSystemService(WINDOW_SERVICE) as WindowManager
        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O)
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
            else
                WindowManager.LayoutParams.TYPE_PHONE,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
            PixelFormat.TRANSLUCENT
        )
        params.gravity = Gravity.TOP or Gravity.START
        params.x = 0
        params.y = 100

        bubbleView = LayoutInflater.from(this).inflate(android.R.layout.simple_list_item_1, null)
        val textView = bubbleView?.findViewById<TextView>(android.R.id.text1)
        textView?.text = "🎥"
        textView?.textSize = 30f
        textView?.setBackgroundColor(0x88000000.toInt())
        
        var initialX = 0
        var initialY = 0
        var initialTouchX = 0f
        var initialTouchY = 0f
        
        bubbleView?.setOnTouchListener { view, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    initialX = params.x
                    initialY = params.y
                    initialTouchX = event.rawX
                    initialTouchY = event.rawY
                    true
                }
                MotionEvent.ACTION_UP -> {
                    val xDiff = Math.abs(event.rawX - initialTouchX)
                    val yDiff = Math.abs(event.rawY - initialTouchY)
                    if (xDiff < 10 && yDiff < 10) {
                        onBubbleTapped()
                    }
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    params.x = initialX + (event.rawX - initialTouchX).toInt()
                    params.y = initialY + (event.rawY - initialTouchY).toInt()
                    windowManager?.updateViewLayout(bubbleView, params)
                    true
                }
                else -> false
            }
        }
        
        windowManager?.addView(bubbleView, params)
        Log.d(TAG, "[Reelix][OVERLAY] bubble shown")
        Log.d(TAG, "[Reelix][SCANNER_STATE] IDLE")
    }

    private fun onBubbleTapped() {
        if (isCapturing) return
        isCapturing = true
        Log.d(TAG, "[Reelix][SCANNER_STATE] CAPTURING")

        thread {
            var audioFinished = false
            thread {
                captureAudio()
                audioFinished = true
            }
            
            captureVisualBurst(targetFrames = 5, durationMs = 2000L)
            
            while(!audioFinished) {
                Thread.sleep(50)
            }
            
            Handler(Looper.getMainLooper()).post {
                Log.d(TAG, "[Reelix][SCANNER_STATE] ANALYZING_PLACEHOLDER")
                
                val intent = Intent("com.reelix.SCAN_RESULT")
                intent.putStringArrayListExtra("frames", ArrayList(capturedFramePaths))
                intent.putExtra("audio", capturedAudioPath)
                sendBroadcast(intent)
                
                isCapturing = false
                Log.d(TAG, "[Reelix][SCANNER_STATE] IDLE")
            }
        }
    }

    private var capturedFramePaths = mutableListOf<String>()
    private var capturedAudioPath: String? = null

    private fun captureVisualBurst(targetFrames: Int, durationMs: Long) {
        capturedFramePaths.clear()
        
        val intervalMs = durationMs / targetFrames
        val startTime = System.currentTimeMillis()
        
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
                // Convert RGBA_8888 to JPEG
                try {
                    val bitmap = android.graphics.Bitmap.createBitmap(width, height, android.graphics.Bitmap.Config.ARGB_8888)
                    bitmap.copyPixelsFromBuffer(java.nio.ByteBuffer.wrap(frameCopy!!))
                    
                    val file = File(cacheDir, "reelix_temp_frame_${System.currentTimeMillis()}_$i.jpg")
                    val out = java.io.FileOutputStream(file)
                    bitmap.compress(android.graphics.Bitmap.CompressFormat.JPEG, 80, out)
                    out.flush()
                    out.close()
                    
                    capturedFramePaths.add(file.absolutePath)
                } catch(e: Exception) {
                    Log.e(TAG, "Error saving JPEG", e)
                }
            }
            
            val elapsed = System.currentTimeMillis() - sampleStartTime
            val waitTime = intervalMs - elapsed
            if (waitTime > 0) {
                Thread.sleep(waitTime)
            }
        }
        
        Log.d(TAG, "[Reelix][VISUAL_CAPTURE] frames_saved=${capturedFramePaths.size}")
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
            header[22] = 1; header[23] = 0 // channels
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
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q && mediaProjection != null) {
            try {
                val config = AudioPlaybackCaptureConfiguration.Builder(mediaProjection!!)
                    .addMatchingUsage(AudioAttributes.USAGE_MEDIA)
                    .addMatchingUsage(AudioAttributes.USAGE_GAME)
                    .addMatchingUsage(AudioAttributes.USAGE_UNKNOWN)
                    .build()

                val audioFormat = AudioFormat.Builder()
                    .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                    .setSampleRate(22050)
                    .setChannelMask(AudioFormat.CHANNEL_IN_MONO)
                    .build()
                    
                val bufferSize = AudioRecord.getMinBufferSize(22050, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT)
                
                audioRecord = AudioRecord.Builder()
                    .setAudioFormat(audioFormat)
                    .setBufferSizeInBytes(bufferSize)
                    .setAudioPlaybackCaptureConfig(config)
                    .build()
                
                audioRecord?.startRecording()
                val buffer = ShortArray(bufferSize)
                var totalSamples = 0
                val durationMs = 2000L // 2 seconds for spike
                val startTime = System.currentTimeMillis()
                
                var isSilent = true
                while (System.currentTimeMillis() - startTime < durationMs) {
                    val read = audioRecord?.read(buffer, 0, buffer.size) ?: 0
                    if (read > 0) {
                        totalSamples += read
                        for (i in 0 until read) {
                            if (buffer[i] > 100 || buffer[i] < -100) {
                                isSilent = false
                                break
                            }
                        }
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
                    capturedAudioPath = saveWavFile(buffer, 22050, totalSamples)
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
        val cacheDir = cacheDir
        val tempFiles = cacheDir.listFiles()
        var deleted = 0
        tempFiles?.forEach {
            if (it.name.startsWith("reelix_temp")) {
                it.delete()
                deleted++
            }
        }
        Log.d(TAG, "[Reelix][TEMP_CLEANUP] success files_deleted=$deleted")
    }

    private fun stopScanner() {
        if (bubbleView != null) {
            windowManager?.removeView(bubbleView)
            bubbleView = null
        }
        
        if (virtualDisplay != null) {
            Log.d(TAG, "[Reelix][VISUAL_CAPTURE] VirtualDisplay releasing")
            virtualDisplay?.release()
            virtualDisplay = null
        }
        
        if (imageReader != null) {
            Log.d(TAG, "[Reelix][VISUAL_CAPTURE] ImageReader releasing")
            imageReader?.close()
            imageReader = null
        }
        
        synchronized(frameLock) {
            latestFrameBytes = null
        }
        
        try {
            audioRecord?.stop()
            audioRecord?.release()
        } catch(e: Exception) {}
        audioRecord = null
        
        if (mediaProjection != null) {
            Log.d(TAG, "[Reelix][MEDIA_PROJECTION] stop() called by our code")
            mediaProjection?.stop()
            mediaProjection = null
        }
        
        cleanupTempData()
    }

    override fun onDestroy() {
        stopScanner()
        super.onDestroy()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val serviceChannel = NotificationChannel(
                CHANNEL_ID,
                "Scanner Service Channel",
                NotificationManager.IMPORTANCE_LOW
            )
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(serviceChannel)
        }
    }
}
