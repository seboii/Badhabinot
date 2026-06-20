package com.badhabinot.backend.dto.admin;

import java.util.List;

/** Sayfalı admin kullanıcı listesi. */
public record AdminUserListResponse(
        List<AdminUserSummary> items,
        long total,
        int page,
        int size
) {
}
