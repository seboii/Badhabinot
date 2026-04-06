package com.badhabinot.monitoring.domain.repository;

import com.badhabinot.monitoring.domain.model.ActivityFeedItem;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ActivityFeedRepository extends JpaRepository<ActivityFeedItem, UUID> {

    List<ActivityFeedItem> findByUserIdOrderByOccurredAtDesc(UUID userId, Pageable pageable);

    List<ActivityFeedItem> findByUserIdAndOccurredAtBetweenOrderByOccurredAtAsc(UUID userId, Instant from, Instant to);
}

