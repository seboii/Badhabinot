package com.badhabinot.backend.service.auth;

import java.util.UUID;

public interface IAccountDeletionService {
    void deleteAccount(UUID userId, String password);
}
