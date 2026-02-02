package com.example.alarmclock

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.GlobalScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import java.time.format.DateTimeFormatter

class MainActivity : ComponentActivity() {

    private val viewModel = AlarmListViewModel()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    AlarmListScreen(viewModel = viewModel)
                }
            }
        }
    }
}

class AlarmListViewModel {
    private val _alarms = MutableStateFlow(listOf<Alarm>())
    val alarms: StateFlow<List<Alarm>> = _alarms

    init {
        val repo = InMemoryAlarmRepository
        GlobalScope.launch {
            repo.upsert(
                Alarm(
                    id = 2,
                    label = "Gym",
                    time = java.time.LocalTime.of(6, 0),
                    recurrence = RecurrencePattern.weekdays(),
                    audioPreference = AudioPreference.SpotifyTrack(
                        uri = "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M",
                        fallbackTone = AudioPreference.LocalTone("default_alarm")
                    ),
                    snoozeMinutes = 5,
                    volumeRampMinutes = 3,
                    vibrationEnabled = true,
                    enabled = true
                )
            )
            _alarms.value = listOfNotNull(repo.getAlarm(1), repo.getAlarm(2))
        }
    }

    fun scheduleAll(context: android.content.Context) {
        val alarmManager = context.getSystemService(android.app.AlarmManager::class.java)
        val scheduler = AlarmScheduler(context, alarmManager)
        alarms.value.forEach { scheduler.schedule(it) }
    }
}

@Composable
fun AlarmListScreen(viewModel: AlarmListViewModel) {
    val alarms by viewModel.alarms.collectAsState()
    val context = LocalContext.current
    Column(
        modifier = Modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        Text(text = "Scheduled Alarms", style = MaterialTheme.typography.headlineSmall)
        LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(alarms) { alarm ->
                AlarmRow(alarm)
            }
        }
        Button(onClick = { viewModel.scheduleAll(context) }) {
            Text("Schedule All")
        }
    }
}

@Composable
fun AlarmRow(alarm: Alarm) {
    val formatter = remember { DateTimeFormatter.ofPattern("EEE h:mm a") }
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(text = alarm.label, style = MaterialTheme.typography.titleMedium)
        Text(
            text = formatter.format(alarm.nextTriggerFrom(java.time.LocalDateTime.now())),
            style = MaterialTheme.typography.bodyMedium
        )
        Text(
            text = when (val pref = alarm.audioPreference) {
                is AudioPreference.LocalTone -> "Tone: ${pref.resName}"
                is AudioPreference.SpotifyTrack -> "Spotify: ${pref.uri}"
            },
            style = MaterialTheme.typography.bodySmall
        )
    }
}
