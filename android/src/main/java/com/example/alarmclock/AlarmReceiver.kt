package com.example.alarmclock

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import androidx.core.content.ContextCompat

class AlarmReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val alarmId = intent.getLongExtra(EXTRA_ALARM_ID, -1L)
        if (alarmId == -1L) return
        val serviceIntent = AlarmService.createIntent(context, alarmId)
        ContextCompat.startForegroundService(context, serviceIntent)
    }

    companion object {
        const val EXTRA_ALARM_ID = "extra_alarm_id"
    }
}
