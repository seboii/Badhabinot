package com.badhabinot.backend.service.auth;

public interface IMailService {
  void sendPasswordResetEmail(String to, String token);
}
