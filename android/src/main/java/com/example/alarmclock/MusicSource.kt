package com.example.alarmclock

import android.content.Context
import android.media.MediaPlayer
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

interface MusicSource {
    val playbackState: StateFlow<PlaybackState>
    suspend fun prepare(context: Context, preference: AudioPreference)
    suspend fun play()
    suspend fun stop()

    sealed class PlaybackState {
        object Idle : PlaybackState()
        object Preparing : PlaybackState()
        data class Playing(val description: String) : PlaybackState()
        data class Error(val throwable: Throwable) : PlaybackState()
    }
}

class LocalToneMusicSource : MusicSource {
    private val state = MutableStateFlow<MusicSource.PlaybackState>(MusicSource.PlaybackState.Idle)
    private var player: MediaPlayer? = null

    override val playbackState: StateFlow<MusicSource.PlaybackState> = state

    override suspend fun prepare(context: Context, preference: AudioPreference) {
        state.value = MusicSource.PlaybackState.Preparing
        val tone = (preference as? AudioPreference.LocalTone)
            ?: throw IllegalArgumentException("LocalToneMusicSource requires LocalTone preference")
        val resId = context.resources.getIdentifier(tone.resName, "raw", context.packageName)
        if (resId == 0) {
            state.value = MusicSource.PlaybackState.Error(IllegalStateException("Missing tone ${tone.resName}"))
            return
        }
        player = MediaPlayer.create(context, resId).apply {
            isLooping = true
        }
        state.value = MusicSource.PlaybackState.Playing("Tone: ${tone.resName}")
    }

    override suspend fun play() {
        player?.start()
    }

    override suspend fun stop() {
        player?.stop()
        player?.release()
        player = null
        state.value = MusicSource.PlaybackState.Idle
    }
}
