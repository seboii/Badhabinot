package com.badhabinot.backend.service.auth;

import java.util.UUID;

public interface IAccountDeletionService {
    /** Kullanıcının kendi hesabını silmesi — şifre doğrulaması gerekir. */
    void deleteAccount(UUID userId, String password);

    /** Admin tarafından hesap silme — hedefin şifresi gerekmez, kaskad silme. */
    void deleteAccountAsAdmin(UUID userId);

    /** Kullanıcı verilerini sıfırla — hesap/profil kalır, izleme + sohbet verisi silinir. */
    void resetUserData(UUID userId);
}
