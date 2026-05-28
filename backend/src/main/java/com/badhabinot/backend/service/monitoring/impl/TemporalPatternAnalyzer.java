package com.badhabinot.backend.service.monitoring.impl;

import com.badhabinot.backend.dto.monitoring.AiChatRequest;
import com.badhabinot.backend.model.monitoring.BehaviorEvent;
import java.time.DayOfWeek;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * Faz 4 — Davranış olaylarından zamansal örüntü çıkarır.
 *
 * Çıktı LLM'e ham olay listesi yerine yapılandırılmış sinyal olarak verilir:
 * "smoking_like_gesture pik saat 10-11, pik gün Pazartesi, son 3 gün artıyor"
 * gibi içgörüler model promptunun grounding'ini güçlendirir.
 *
 * Saf yardımcı sınıf — DI dışında, ChatContextBuilderServiceImpl tarafından
 * doğrudan çağrılır.
 */
final class TemporalPatternAnalyzer {

    private static final int MIN_EVENTS_FOR_PATTERN = 3;
    private static final double TREND_THRESHOLD = 0.30;   // ±%30 → yön
    private static final int RECENT_WINDOW_DAYS = 3;
    private static final int PRIOR_WINDOW_DAYS = 4;

    private TemporalPatternAnalyzer() {
    }

    /**
     * Olay listesinden her event_type için bir BehavioralPattern üretir.
     *
     * @param events       Son N olay (occurredAt sıralaması umursanmaz)
     * @param zoneId       Kullanıcının zaman dilimi (saat/gün yerel hesap)
     * @param referenceDate Trend referans günü (genellikle currentReport.reportDate())
     * @return Her event_type için bir pattern; toplam olay sayısına göre azalan sıralı
     */
    static List<AiChatRequest.BehavioralPattern> analyze(
            List<BehaviorEvent> events,
            ZoneId zoneId,
            LocalDate referenceDate
    ) {
        if (events == null || events.isEmpty()) {
            return List.of();
        }

        Map<String, List<BehaviorEvent>> byType = events.stream()
                .filter(event -> event.getEventType() != null && event.getOccurredAt() != null)
                .collect(Collectors.groupingBy(BehaviorEvent::getEventType));

        return byType.entrySet().stream()
                .filter(entry -> entry.getValue().size() >= MIN_EVENTS_FOR_PATTERN)
                .map(entry -> buildPattern(entry.getKey(), entry.getValue(), zoneId, referenceDate))
                .sorted(Comparator.comparingInt(AiChatRequest.BehavioralPattern::totalCountLast7Days).reversed())
                .toList();
    }

    private static AiChatRequest.BehavioralPattern buildPattern(
            String eventType,
            List<BehaviorEvent> sameTypeEvents,
            ZoneId zoneId,
            LocalDate referenceDate
    ) {
        Map<Integer, Integer> hourHistogram = new HashMap<>();
        Map<DayOfWeek, Integer> dayHistogram = new EnumMap<>(DayOfWeek.class);

        int recentCount = 0;
        int priorCount = 0;
        LocalDate recentStart = referenceDate.minusDays(RECENT_WINDOW_DAYS - 1);
        LocalDate priorStart = recentStart.minusDays(PRIOR_WINDOW_DAYS);

        for (BehaviorEvent event : sameTypeEvents) {
            ZonedDateTime local = event.getOccurredAt().atZone(zoneId);
            hourHistogram.merge(local.getHour(), 1, Integer::sum);
            dayHistogram.merge(local.getDayOfWeek(), 1, Integer::sum);

            LocalDate eventDate = local.toLocalDate();
            if (!eventDate.isBefore(recentStart) && !eventDate.isAfter(referenceDate)) {
                recentCount++;
            } else if (!eventDate.isBefore(priorStart) && eventDate.isBefore(recentStart)) {
                priorCount++;
            }
        }

        Map.Entry<Integer, Integer> peakHour = peakEntry(hourHistogram, 0);
        Map.Entry<DayOfWeek, Integer> peakDay = peakEntry(dayHistogram, DayOfWeek.MONDAY);

        return new AiChatRequest.BehavioralPattern(
                eventType,
                peakHour.getKey(),
                peakHour.getValue(),
                peakDay.getKey().name(),
                peakDay.getValue(),
                sameTypeEvents.size(),
                intensityLabel(sameTypeEvents.size()),
                trendLabel(recentCount, priorCount)
        );
    }

    private static <K> Map.Entry<K, Integer> peakEntry(Map<K, Integer> histogram, K fallback) {
        return histogram.entrySet().stream()
                .max(Comparator.comparingInt(Map.Entry::getValue))
                .orElseGet(() -> Map.entry(fallback, 0));
    }

    private static String intensityLabel(int total) {
        if (total >= 12) {
            return "yogun";
        }
        if (total >= 5) {
            return "orta";
        }
        return "az";
    }

    private static String trendLabel(int recentCount, int priorCount) {
        // Normalize to per-day so window length farkı bozmasın.
        double recentRate = recentCount / (double) RECENT_WINDOW_DAYS;
        double priorRate = priorCount / (double) PRIOR_WINDOW_DAYS;
        if (priorRate <= 0.0 && recentRate <= 0.0) {
            return "stabil";
        }
        if (priorRate <= 0.0) {
            return "artiyor";
        }
        double change = (recentRate - priorRate) / priorRate;
        if (change >= TREND_THRESHOLD) {
            return "artiyor";
        }
        if (change <= -TREND_THRESHOLD) {
            return "azaliyor";
        }
        return "stabil";
    }
}
