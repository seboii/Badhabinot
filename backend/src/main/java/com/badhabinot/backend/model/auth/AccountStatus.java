package com.badhabinot.backend.model.auth;

public enum AccountStatus {
    /** Yeni kayıt — yönetici onayı bekliyor; onaylanana kadar giriş yapamaz. */
    PENDING_APPROVAL,
    ACTIVE,
    LOCKED,
    DISABLED
}


