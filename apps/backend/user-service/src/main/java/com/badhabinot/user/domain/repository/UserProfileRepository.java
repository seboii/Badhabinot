package com.badhabinot.user.domain.repository;

import com.badhabinot.user.domain.model.UserProfile;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserProfileRepository extends JpaRepository<UserProfile, UUID> {
}

