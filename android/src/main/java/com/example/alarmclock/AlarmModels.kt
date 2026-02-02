package com.example.alarmclock

import java.time.DayOfWeek
import java.time.LocalDateTime
import java.time.LocalTime
import java.time.temporal.TemporalAdjusters

/** Domain models representing an alarm and its audio preferences. */
data class Alarm(
    val id: Long,
    val label: String,
    val time: LocalTime,
    val recurrence: RecurrencePattern,
    val audioPreference: AudioPreference,
    val snoozeMinutes: Int,
    val volumeRampMinutes: Int?,
    val vibrationEnabled: Boolean,
    val enabled: Boolean
) {
    fun nextTriggerFrom(now: LocalDateTime): LocalDateTime {
        val baseDate = now.toLocalDate()
        val todayTrigger = LocalDateTime.of(baseDate, time)
        if (recurrence.isOneShot) {
            return if (todayTrigger > now) todayTrigger else todayTrigger.plusDays(1)
        }

        val candidates = recurrence.days.map { day ->
            val nextDate = baseDate.with(TemporalAdjusters.nextOrSame(day))
            var candidate = LocalDateTime.of(nextDate, time)
            if (candidate <= now) {
                candidate = LocalDateTime.of(nextDate.plusWeeks(1), time)
            }
            candidate
        }
        return candidates.minByOrNull { it } ?: todayTrigger
    }
}

sealed interface AudioPreference {
    data class LocalTone(val resName: String) : AudioPreference
    data class SpotifyTrack(
        val uri: String,
        val fallbackTone: LocalTone,
        val startOffsetMs: Int = 0
    ) : AudioPreference
}

data class RecurrencePattern(val days: Set<DayOfWeek>) {
    val isOneShot: Boolean = days.isEmpty()

    companion object {
        fun oneShot(): RecurrencePattern = RecurrencePattern(emptySet())
        fun weekdays(): RecurrencePattern = RecurrencePattern(
            setOf(
                DayOfWeek.MONDAY,
                DayOfWeek.TUESDAY,
                DayOfWeek.WEDNESDAY,
                DayOfWeek.THURSDAY,
                DayOfWeek.FRIDAY
            )
        )
    }
}
