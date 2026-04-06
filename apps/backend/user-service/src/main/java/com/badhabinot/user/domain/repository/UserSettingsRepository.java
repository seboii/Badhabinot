package com.badhabinot.user.domain.repository;

import com.badhabinot.user.domain.model.UserSettings;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserSettingsRepository extends JpaRepository<UserSettings, UUID> {
}

