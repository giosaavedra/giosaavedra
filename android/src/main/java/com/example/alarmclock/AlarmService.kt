package com.example.alarmclock

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class AlarmService : Service() {

    private val job = Job()
    private val scope = CoroutineScope(Dispatchers.Main + job)
    private lateinit var repository: AlarmRepository
    private lateinit var localMusicSource: LocalToneMusicSource
    private lateinit var spotifyMusicSource: SpotifyMusicSource
    private var activeSource: MusicSource? = null

    override fun onCreate() {
        super.onCreate()
        repository = InMemoryAlarmRepository // replace with DI in production
        localMusicSource = LocalToneMusicSource()
        spotifyMusicSource = SpotifyMusicSource(
            clientId = BuildConfigHolder.spotifyClientId,
            redirectUri = BuildConfigHolder.spotifyRedirectUri
        )
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val alarmId = intent?.getLongExtra(EXTRA_ALARM_ID, -1L) ?: -1L
        if (alarmId == -1L) return START_NOT_STICKY
        scope.launch {
            val alarm = repository.getAlarm(alarmId) ?: return@launch stopSelf()
            startForeground(NOTIFICATION_ID, buildNotification(alarm.label, "Preparing"))
            playAlarm(alarm)
        }
        return START_STICKY
    }

    override fun onDestroy() {
        super.onDestroy()
        scope.launch { activeSource?.stop() }
        job.cancel()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private suspend fun playAlarm(alarm: Alarm) {
        val source = selectMusicSource(alarm.audioPreference)
        activeSource = source
        source.prepare(this, alarm.audioPreference)
        val state = source.playbackState.value
        if (state is MusicSource.PlaybackState.Error && alarm.audioPreference is AudioPreference.SpotifyTrack) {
            val fallbackTone = alarm.audioPreference.fallbackTone
            localMusicSource.prepare(this, fallbackTone)
            activeSource = localMusicSource
            localMusicSource.play()
            NotificationManagerCompat.from(this)
                .notify(NOTIFICATION_ID, buildNotification(alarm.label, "Fallback tone"))
            return
        }
        source.play()
        NotificationManagerCompat.from(this)
            .notify(NOTIFICATION_ID, buildNotification(alarm.label, "Playing"))
    }

    private fun selectMusicSource(preference: AudioPreference): MusicSource =
        when (preference) {
            is AudioPreference.LocalTone -> localMusicSource
            is AudioPreference.SpotifyTrack -> spotifyMusicSource
        }

    private fun buildNotification(title: String, subtitle: String): Notification =
        NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_lock_idle_alarm)
            .setContentTitle(title)
            .setContentText(subtitle)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setOngoing(true)
            .build()

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Active Alarms",
                NotificationManager.IMPORTANCE_HIGH
            )
            getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
        }
    }

    companion object {
        private const val CHANNEL_ID = "alarms"
        private const val NOTIFICATION_ID = 42
        private const val EXTRA_ALARM_ID = "extra_alarm_id"

        fun createIntent(context: Context, alarmId: Long): Intent =
            Intent(context, AlarmService::class.java).apply {
                putExtra(EXTRA_ALARM_ID, alarmId)
            }
    }
}

/**
 * Placeholder repository. Replace with Room-backed implementation.
 */
interface AlarmRepository {
    suspend fun getAlarm(id: Long): Alarm?
    suspend fun upsert(alarm: Alarm)
}

object InMemoryAlarmRepository : AlarmRepository {
    private val alarms = mutableMapOf<Long, Alarm>()

    init {
        val sample = Alarm(
            id = 1,
            label = "Morning Alarm",
            time = java.time.LocalTime.of(7, 0),
            recurrence = RecurrencePattern.weekdays(),
            audioPreference = AudioPreference.LocalTone("default_alarm"),
            snoozeMinutes = 10,
            volumeRampMinutes = 5,
            vibrationEnabled = true,
            enabled = true
        )
        alarms[sample.id] = sample
    }

    override suspend fun getAlarm(id: Long): Alarm? = withContext(Dispatchers.IO) { alarms[id] }
    override suspend fun upsert(alarm: Alarm) {
        withContext(Dispatchers.IO) { alarms[alarm.id] = alarm }
    }
}

/**
 * Simple holder for build constants so the sample can compile without Gradle.
 */
object BuildConfigHolder {
    var spotifyClientId: String = "YOUR_SPOTIFY_CLIENT_ID"
    var spotifyRedirectUri: String = "yourapp://callback"
}
