package com.badhabinot.backend.service.monitoring.impl;

import static org.assertj.core.api.Assertions.assertThat;

import com.badhabinot.backend.dto.monitoring.AiChatRequest;
import com.badhabinot.backend.model.monitoring.BehaviorEvent;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.Test;

/**
 * Faz 4 — TemporalPatternAnalyzer testleri.
 *
 * Saf yardımcı sınıf, mock gerekmez; gerçek BehaviorEvent instance'larıyla çalışır.
 */
class TemporalPatternAnalyzerTest {

    private static final ZoneId TR = ZoneId.of("Europe/Istanbul");
    private static final LocalDate TODAY = LocalDate.of(2026, 5, 28);

    private static BehaviorEvent event(String type, ZonedDateTime when) {
        return BehaviorEvent.create(
                UUID.randomUUID(),
                UUID.randomUUID(),
                UUID.randomUUID(),
                type,
                "test",
                0.8,
                "medium",
                "test",
                "test",
                "{}",
                when.toInstant()
        );
    }

    @Test
    void emptyEventListReturnsEmptyPatternList() {
        List<AiChatRequest.BehavioralPattern> patterns =
                TemporalPatternAnalyzer.analyze(List.of(), TR, TODAY);
        assertThat(patterns).isEmpty();
    }

    @Test
    void belowMinThresholdEventTypeIsExcluded() {
        // Sadece 2 olay var — eşik 3, dışlanmalı.
        List<BehaviorEvent> events = List.of(
                event("smoking_like_gesture", TODAY.atTime(10, 0).atZone(TR)),
                event("smoking_like_gesture", TODAY.atTime(11, 0).atZone(TR))
        );
        var patterns = TemporalPatternAnalyzer.analyze(events, TR, TODAY);
        assertThat(patterns).isEmpty();
    }

    @Test
    void peakHourAndDayCorrectlyIdentified() {
        // 5 olay sigara: 3 tanesi saat 10'da (Pazartesi 25 Mayıs)
        LocalDate monday = LocalDate.of(2026, 5, 25);
        List<BehaviorEvent> events = new ArrayList<>();
        events.add(event("smoking_like_gesture", monday.atTime(10, 5).atZone(TR)));
        events.add(event("smoking_like_gesture", monday.atTime(10, 20).atZone(TR)));
        events.add(event("smoking_like_gesture", monday.atTime(10, 50).atZone(TR)));
        events.add(event("smoking_like_gesture", TODAY.atTime(14, 0).atZone(TR)));
        events.add(event("smoking_like_gesture", TODAY.atTime(18, 0).atZone(TR)));

        var patterns = TemporalPatternAnalyzer.analyze(events, TR, TODAY);
        assertThat(patterns).hasSize(1);
        var p = patterns.get(0);
        assertThat(p.eventType()).isEqualTo("smoking_like_gesture");
        assertThat(p.peakHourOfDay()).isEqualTo(10);
        assertThat(p.peakHourCount()).isEqualTo(3);
        assertThat(p.peakDayOfWeek()).isEqualTo("MONDAY");
        assertThat(p.peakDayCount()).isEqualTo(3);
        assertThat(p.totalCountLast7Days()).isEqualTo(5);
    }

    @Test
    void intensityLabelReflectsTotalCount() {
        // 12+ = yogun, 5-11 = orta, 3-4 = az
        assertThat(buildPattern(15).intensityLabel()).isEqualTo("yogun");
        assertThat(buildPattern(7).intensityLabel()).isEqualTo("orta");
        assertThat(buildPattern(3).intensityLabel()).isEqualTo("az");
    }

    @Test
    void trendIncreasingWhenRecentRateExceedsPriorByThreshold() {
        // Son 3 gün: 6 olay (rate 2/day). Önceki 4 gün: 2 olay (rate 0.5/day). +%300 → artiyor.
        List<BehaviorEvent> events = new ArrayList<>();
        for (int i = 0; i < 6; i++) {
            events.add(event("hand_movement_pattern", TODAY.minusDays(i % 3).atTime(10, i).atZone(TR)));
        }
        events.add(event("hand_movement_pattern", TODAY.minusDays(5).atTime(10, 0).atZone(TR)));
        events.add(event("hand_movement_pattern", TODAY.minusDays(6).atTime(10, 0).atZone(TR)));

        var patterns = TemporalPatternAnalyzer.analyze(events, TR, TODAY);
        assertThat(patterns).hasSize(1);
        assertThat(patterns.get(0).trendLabel()).isEqualTo("artiyor");
    }

    @Test
    void trendDecreasingWhenRecentRateBelowPriorByThreshold() {
        // Son 3 gün: 1 olay. Önceki 4 gün: 8 olay (rate 2/day vs 0.33/day). −%83 → azaliyor.
        List<BehaviorEvent> events = new ArrayList<>();
        events.add(event("poor_posture", TODAY.atTime(10, 0).atZone(TR)));
        for (int i = 0; i < 8; i++) {
            events.add(event("poor_posture", TODAY.minusDays(3 + (i % 4)).atTime(9, i).atZone(TR)));
        }

        var patterns = TemporalPatternAnalyzer.analyze(events, TR, TODAY);
        assertThat(patterns).hasSize(1);
        assertThat(patterns.get(0).trendLabel()).isEqualTo("azaliyor");
    }

    @Test
    void patternsAreSortedByTotalCountDescending() {
        List<BehaviorEvent> events = new ArrayList<>();
        // smoking_like: 3 olay
        for (int i = 0; i < 3; i++) {
            events.add(event("smoking_like_gesture", TODAY.atTime(10, i).atZone(TR)));
        }
        // poor_posture: 7 olay → en üstte olmalı
        for (int i = 0; i < 7; i++) {
            events.add(event("poor_posture", TODAY.minusDays(i % 3).atTime(15, i).atZone(TR)));
        }

        var patterns = TemporalPatternAnalyzer.analyze(events, TR, TODAY);
        assertThat(patterns).hasSize(2);
        assertThat(patterns.get(0).eventType()).isEqualTo("poor_posture");
        assertThat(patterns.get(0).totalCountLast7Days()).isEqualTo(7);
        assertThat(patterns.get(1).eventType()).isEqualTo("smoking_like_gesture");
    }

    private static AiChatRequest.BehavioralPattern buildPattern(int count) {
        List<BehaviorEvent> events = new ArrayList<>();
        for (int i = 0; i < count; i++) {
            events.add(event("x", TODAY.atTime(10, i).atZone(TR)));
        }
        return TemporalPatternAnalyzer.analyze(events, TR, TODAY).get(0);
    }
}
