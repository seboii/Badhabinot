package com.badhabinot.backend.dto.admin;

import com.badhabinot.backend.model.user.ChatPersona;
import com.badhabinot.backend.model.user.ModelMode;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

/** Admin'in bir kullanıcının AI/sohbet ayarlarını düzenlemesi (API/LOCAL vb.). */
public record AdminUserAiSettingsRequest(
        @NotNull ModelMode modelMode,
        @Size(max = 100) String localModelName,
        @Size(max = 255) String ollamaBaseUrl,
        ChatPersona chatPersona
) {
}
