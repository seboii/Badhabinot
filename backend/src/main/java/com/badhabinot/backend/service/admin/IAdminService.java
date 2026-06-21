package com.badhabinot.backend.service.admin;

import com.badhabinot.backend.dto.admin.AdminReportSummary;
import com.badhabinot.backend.dto.admin.AdminStats;
import com.badhabinot.backend.dto.admin.AdminUserAiSettingsRequest;
import com.badhabinot.backend.dto.admin.AdminUserDetail;
import com.badhabinot.backend.dto.admin.AdminUserListResponse;
import java.util.List;
import java.util.UUID;

/** Admin paneli işlemleri — tüm kullanıcıların verilerini görüntüleme ve yönetme. */
public interface IAdminService {

    AdminUserListResponse listUsers(String search, int page, int size);

    AdminUserDetail getUserDetail(UUID userId);

    List<AdminReportSummary> getUserReports(UUID userId, int limit);

    void deleteUser(UUID userId);

    void resetUserData(UUID userId);

    /** Onay bekleyen kullanıcıyı aktifleştir (PENDING_APPROVAL → ACTIVE). */
    void approveUser(UUID userId);

    /** Bir kullanıcının AI/sohbet ayarlarını (API/LOCAL mod, model, ollama URL) güncelle. */
    void updateUserAiSettings(UUID userId, AdminUserAiSettingsRequest request);

    AdminStats getStats();
}
