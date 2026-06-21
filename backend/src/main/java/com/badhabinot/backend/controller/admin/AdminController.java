package com.badhabinot.backend.controller.admin;

import com.badhabinot.backend.dto.admin.AdminReportSummary;
import com.badhabinot.backend.dto.admin.AdminStats;
import com.badhabinot.backend.dto.admin.AdminUserAiSettingsRequest;
import com.badhabinot.backend.dto.admin.AdminUserDetail;
import com.badhabinot.backend.dto.admin.AdminUserListResponse;
import com.badhabinot.backend.service.admin.IAdminService;
import jakarta.validation.Valid;
import java.util.List;
import java.util.UUID;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * Admin paneli REST API'si. Tüm uçlar yalnızca ROLE_ADMIN için erişilebilir
 * (hem buradaki @PreAuthorize hem SecurityConfiguration matcher ile korunur).
 */
@RestController
@RequestMapping("/api/v1/admin")
@PreAuthorize("hasRole('ADMIN')")
public class AdminController {

    private final IAdminService adminService;

    public AdminController(IAdminService adminService) {
        this.adminService = adminService;
    }

    @GetMapping("/stats")
    public AdminStats stats() {
        return adminService.getStats();
    }

    @GetMapping("/users")
    public AdminUserListResponse listUsers(
            @RequestParam(required = false) String search,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size
    ) {
        return adminService.listUsers(search, page, size);
    }

    @GetMapping("/users/{userId}")
    public AdminUserDetail userDetail(@PathVariable UUID userId) {
        return adminService.getUserDetail(userId);
    }

    @GetMapping("/users/{userId}/reports")
    public List<AdminReportSummary> userReports(
            @PathVariable UUID userId,
            @RequestParam(defaultValue = "30") int limit
    ) {
        return adminService.getUserReports(userId, limit);
    }

    @DeleteMapping("/users/{userId}")
    public ResponseEntity<Void> deleteUser(@PathVariable UUID userId) {
        adminService.deleteUser(userId);
        return ResponseEntity.noContent().build();
    }

    @PostMapping("/users/{userId}/reset")
    public ResponseEntity<Void> resetUserData(@PathVariable UUID userId) {
        adminService.resetUserData(userId);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/users/{userId}/approve")
    public ResponseEntity<Void> approveUser(@PathVariable UUID userId) {
        adminService.approveUser(userId);
        return ResponseEntity.ok().build();
    }

    @PutMapping("/users/{userId}/ai-settings")
    public ResponseEntity<Void> updateUserAiSettings(
            @PathVariable UUID userId,
            @Valid @RequestBody AdminUserAiSettingsRequest request
    ) {
        adminService.updateUserAiSettings(userId, request);
        return ResponseEntity.ok().build();
    }
}
