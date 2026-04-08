package com.badhabinot.backend.controller.user;

import com.badhabinot.backend.dto.user.InternalUserAnalysisContextResponse;
import com.badhabinot.backend.dto.user.InternalUserBootstrapRequest;
import com.badhabinot.backend.service.user.UserContextService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/internal/users")
@Tag(name = "Internal Users", description = "Internal-only user bootstrap and analysis context APIs")
public class InternalUserController {

    private final UserContextService userContextService;

    public InternalUserController(UserContextService userContextService) {
        this.userContextService = userContextService;
    }

    @PostMapping("/bootstrap")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @Operation(summary = "Bootstrap user profile for internal backend flows")
    public void bootstrap(@Valid @RequestBody InternalUserBootstrapRequest request) {
        userContextService.bootstrap(request);
    }

    @GetMapping("/{userId}/analysis-context")
    @Operation(summary = "Return internal analysis settings for monitoring workflows")
    public InternalUserAnalysisContextResponse analysisContext(@PathVariable("userId") UUID userId) {
        return userContextService.getInternalAnalysisContext(userId);
    }
}
