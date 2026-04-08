package com.badhabinot.backend.repository.user;

import com.badhabinot.backend.model.user.UserConsent;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserConsentRepository extends JpaRepository<UserConsent, UUID> {
}


