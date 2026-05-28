package com.badhabinot.backend.repository.monitoring;

import com.badhabinot.backend.model.monitoring.PushToken;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface PushTokenRepository extends JpaRepository<PushToken, UUID> {

    Optional<PushToken> findByToken(String token);

    List<PushToken> findByUserIdAndActiveTrue(UUID userId);

    @Modifying
    @Query("UPDATE PushToken t SET t.active = false WHERE t.token = :token")
    void deactivateByToken(@Param("token") String token);

    @Modifying
    @Query("DELETE FROM PushToken t WHERE t.userId = :userId")
    void deleteByUserId(@Param("userId") UUID userId);
}
