package com.badhabinot.backend.service.auth;

public interface IMailService {
  void sendPasswordResetEmail(String to, String token);

  /** Yeni bir kullanıcı kaydolup onay beklediğinde yöneticiye bilgi e-postası gönderir. */
  void sendNewUserNotification(String newUserEmail);
}
