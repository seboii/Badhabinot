package com.badhabinot.user.domain.repository;

import com.badhabinot.user.domain.model.UserConsent;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserConsentRepository extends JpaRepository<UserConsent, UUID> {
}

