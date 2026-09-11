package com.reelix.reelix

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.media.projection.MediaProjectionManager
import android.net.Uri
import android.os.Build
import android.provider.Settings
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import android.Manifest
import android.content.pm.PackageManager
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat

class MainActivity: FlutterActivity() {
    private val CHANNEL = "com.reelix.reelix/scanner"
    private val OVERLAY_PERMISSION_REQ_CODE = 1001
    private val MEDIA_PROJECTION_REQ_CODE = 1002
    private val AUDIO_PERMISSION_REQ_CODE = 1003
    private val NOTIFICATION_PERMISSION_REQ_CODE = 1004

    private var pendingResult: MethodChannel.Result? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL).setMethodCallHandler { call, result ->
            when (call.method) {
                "checkOverlayPermission" -> {
                    result.success(Settings.canDrawOverlays(this))
                }
                "requestOverlayPermission" -> {
                    if (!Settings.canDrawOverlays(this)) {
                        val intent = Intent(
                            Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                            Uri.parse("package:$packageName")
                        )
                        startActivityForResult(intent, OVERLAY_PERMISSION_REQ_CODE)
                        pendingResult = result
                    } else {
                        result.success(true)
                    }
                }
                "checkAudioPermission" -> {
                    val granted = ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED
                    result.success(granted)
                }
                "requestAudioPermission" -> {
                    if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
                        pendingResult = result
                        ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.RECORD_AUDIO), AUDIO_PERMISSION_REQ_CODE)
                    } else {
                        result.success(true)
                    }
                }
                "checkNotificationPermission" -> {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                        val granted = ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED
                        result.success(granted)
                    } else {
                        result.success(true)
                    }
                }
                "requestNotificationPermission" -> {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                        if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                            pendingResult = result
                            ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.POST_NOTIFICATIONS), NOTIFICATION_PERMISSION_REQ_CODE)
                        } else {
                            result.success(true)
                        }
                    } else {
                        result.success(true)
                    }
                }
                "startScanner" -> {
                    startMediaProjectionRequest(result)
                }
                "stopScanner" -> {
                    val intent = Intent(this, ScannerService::class.java)
                    intent.action = ScannerService.ACTION_STOP
                    startService(intent)
                    result.success(true)
                }
                "cleanupTemp" -> {
                    val cacheDir = cacheDir
                    val tempFiles = cacheDir.listFiles()
                    var deleted = 0
                    tempFiles?.forEach {
                        if (it.name.startsWith("reelix_temp")) {
                            it.delete()
                            deleted++
                        }
                    }
                    result.success(deleted)
                }
                else -> {
                    result.notImplemented()
                }
            }
        }
        
        val receiver = object : android.content.BroadcastReceiver() {
            override fun onReceive(context: Context?, intent: Intent?) {
                if (intent?.action == "com.reelix.SCAN_RESULT") {
                    val frames = intent.getStringArrayListExtra("frames")
                    val audio = intent.getStringExtra("audio")
                    
                    val map = mapOf(
                        "frames" to frames,
                        "audio" to audio
                    )
                    MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL).invokeMethod("onScanResult", map)
                }
            }
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            registerReceiver(receiver, android.content.IntentFilter("com.reelix.SCAN_RESULT"), Context.RECEIVER_NOT_EXPORTED)
        } else {
            registerReceiver(receiver, android.content.IntentFilter("com.reelix.SCAN_RESULT"))
        }
    }

    private fun startMediaProjectionRequest(result: MethodChannel.Result) {
        val projectionManager = getSystemService(Context.MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
        startActivityForResult(projectionManager.createScreenCaptureIntent(), MEDIA_PROJECTION_REQ_CODE)
        pendingResult = result
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        when (requestCode) {
            OVERLAY_PERMISSION_REQ_CODE -> {
                pendingResult?.success(Settings.canDrawOverlays(this))
                pendingResult = null
            }
            MEDIA_PROJECTION_REQ_CODE -> {
                if (resultCode == Activity.RESULT_OK && data != null) {
                    val intent = Intent(this, ScannerService::class.java)
                    intent.action = ScannerService.ACTION_START
                    intent.putExtra(ScannerService.EXTRA_RESULT_CODE, resultCode)
                    intent.putExtra(ScannerService.EXTRA_RESULT_DATA, data)
                    
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                        startForegroundService(intent)
                    } else {
                        startService(intent)
                    }
                    pendingResult?.success(true)
                } else {
                    pendingResult?.success(false)
                }
                pendingResult = null
            }
        }
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        when (requestCode) {
            AUDIO_PERMISSION_REQ_CODE -> {
                val granted = grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED
                pendingResult?.success(granted)
                pendingResult = null
            }
            NOTIFICATION_PERMISSION_REQ_CODE -> {
                val granted = grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED
                pendingResult?.success(granted)
                pendingResult = null
            }
        }
    }
}
