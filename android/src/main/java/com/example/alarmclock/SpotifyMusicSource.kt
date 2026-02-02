package com.example.alarmclock

import android.content.Context
import com.spotify.android.appremote.api.ConnectionParams
import com.spotify.android.appremote.api.SpotifyAppRemote
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeoutOrNull
import kotlin.coroutines.resume

class SpotifyMusicSource(
    private val clientId: String,
    private val redirectUri: String
) : MusicSource {

    private val state = MutableStateFlow<MusicSource.PlaybackState>(MusicSource.PlaybackState.Idle)
    override val playbackState: StateFlow<MusicSource.PlaybackState> = state

    private var appRemote: SpotifyAppRemote? = null
    private var currentPreference: AudioPreference.SpotifyTrack? = null

    override suspend fun prepare(context: Context, preference: AudioPreference) {
        val spotifyPref = preference as? AudioPreference.SpotifyTrack
            ?: throw IllegalArgumentException("SpotifyMusicSource requires SpotifyTrack preference")
        currentPreference = spotifyPref
        state.value = MusicSource.PlaybackState.Preparing
        val connectionParams = ConnectionParams.Builder(clientId)
            .setRedirectUri(redirectUri)
            .showAuthView(true)
            .build()

        val remote = withContext(Dispatchers.Main) {
            withTimeoutOrNull(5000) {
                SpotifyAppRemote.connectSuspend(context, connectionParams)
            }
        }

        if (remote == null) {
            state.value = MusicSource.PlaybackState.Error(IllegalStateException("Spotify connection timeout"))
            return
        }
        appRemote = remote
        state.value = MusicSource.PlaybackState.Playing("Spotify track ${spotifyPref.uri}")
    }

    override suspend fun play() {
        val pref = currentPreference ?: return
        val remote = appRemote ?: return
        withContext(Dispatchers.Main) {
            remote.playerApi.play(pref.uri)
            if (pref.startOffsetMs > 0) {
                remote.playerApi.seekTo(pref.startOffsetMs.toLong())
            }
        }
    }

    override suspend fun stop() {
        val remote = appRemote
        state.value = MusicSource.PlaybackState.Idle
        withContext(Dispatchers.Main) {
            remote?.playerApi?.pause()
            remote?.let { SpotifyAppRemote.disconnect(it) }
        }
        appRemote = null
    }
}

private suspend fun SpotifyAppRemote.Companion.connectSuspend(
    context: Context,
    params: ConnectionParams
): SpotifyAppRemote = suspendCancellableCoroutine { continuation ->
    connect(context, params, object : com.spotify.android.appremote.api.Connector.ConnectionListener {
        override fun onConnected(spotifyAppRemote: SpotifyAppRemote) {
            continuation.resume(spotifyAppRemote)
        }

        override fun onFailure(throwable: Throwable) {
            if (continuation.isActive) continuation.resumeWith(Result.failure(throwable))
        }
    })
}
