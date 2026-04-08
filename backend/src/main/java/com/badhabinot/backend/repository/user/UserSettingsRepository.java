package com.badhabinot.backend.repository.user;

import com.badhabinot.backend.model.user.UserSettings;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserSettingsRepository extends JpaRepository<UserSettings, UUID> {
}


