package com.reelix.reelix

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.media.projection.MediaProjectionManager
import android.os.Bundle
import android.util.Log

class CaptureConsentActivity : Activity() {
    private val MEDIA_PROJECTION_REQ_CODE = 2002

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        Log.d("ReelixScanner", "[Reelix][PROJECTION] consent_requested")
        val projectionManager = getSystemService(Context.MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
        startActivityForResult(projectionManager.createScreenCaptureIntent(), MEDIA_PROJECTION_REQ_CODE)
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == MEDIA_PROJECTION_REQ_CODE) {
            if (resultCode == RESULT_OK && data != null) {
                Log.d("ReelixScanner", "[Reelix][PROJECTION] consent_granted")
                val serviceIntent = Intent(this, ScannerService::class.java)
                serviceIntent.action = ScannerService.ACTION_START_PROJECTION
                serviceIntent.putExtra(ScannerService.EXTRA_RESULT_CODE, resultCode)
                serviceIntent.putExtra(ScannerService.EXTRA_RESULT_DATA, data)
                startService(serviceIntent)
            } else {
                Log.d("ReelixScanner", "[Reelix][PROJECTION] consent_denied")
            }
            finish()
        }
    }
}
