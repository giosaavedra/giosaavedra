package com.example.alarmclock

import android.app.AlarmManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import java.time.LocalDateTime
import java.time.ZoneId

class AlarmScheduler(private val context: Context, private val alarmManager: AlarmManager) {

    fun schedule(alarm: Alarm) {
        if (!alarm.enabled) return
        val triggerTime = alarm.nextTriggerFrom(LocalDateTime.now())
        val requestCode = alarm.id.toInt()
        val pendingIntent = createPendingIntent(alarm, requestCode)
        alarmManager.setExactAndAllowWhileIdle(
            AlarmManager.RTC_WAKEUP,
            triggerTime.atZone(ZoneId.systemDefault()).toInstant().toEpochMilli(),
            pendingIntent
        )
    }

    fun cancel(alarmId: Long) {
        val pendingIntent = createPendingIntent(alarmId)
        alarmManager.cancel(pendingIntent)
        pendingIntent.cancel()
    }

    private fun createPendingIntent(alarm: Alarm, requestCode: Int): PendingIntent {
        val intent = Intent(context, AlarmReceiver::class.java).apply {
            action = ACTION_TRIGGER_ALARM
            putExtra(AlarmReceiver.EXTRA_ALARM_ID, alarm.id)
        }
        return PendingIntent.getBroadcast(
            context,
            requestCode,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
    }

    private fun createPendingIntent(alarmId: Long): PendingIntent {
        val intent = Intent(context, AlarmReceiver::class.java).apply {
            action = ACTION_TRIGGER_ALARM
            putExtra(AlarmReceiver.EXTRA_ALARM_ID, alarmId)
        }
        return PendingIntent.getBroadcast(
            context,
            alarmId.toInt(),
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
    }

    companion object {
        const val ACTION_TRIGGER_ALARM = "com.example.alarmclock.ACTION_TRIGGER_ALARM"
    }
}
