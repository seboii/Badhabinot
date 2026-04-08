package com.badhabinot.backend.repository.auth;

import com.badhabinot.backend.model.auth.AuthUser;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AuthUserRepository extends JpaRepository<AuthUser, UUID> {

    boolean existsByEmail(String email);

    Optional<AuthUser> findByEmail(String email);
}


