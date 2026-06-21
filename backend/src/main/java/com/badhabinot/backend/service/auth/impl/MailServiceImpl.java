package com.badhabinot.backend.service.auth.impl;

import com.badhabinot.backend.config.PasswordResetProperties;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.MailException;
import org.springframework.mail.javamail.JavaMailSender;
import com.badhabinot.backend.service.auth.IMailService;
import org.springframework.stereotype.Service;

@Service
public class MailServiceImpl implements IMailService {

    private static final Logger log = LoggerFactory.getLogger(MailServiceImpl.class);

    private final JavaMailSender mailSender;
    private final PasswordResetProperties properties;

    /** Yeni kayıt bildirimlerinin gideceği yönetici adresi. */
    @Value("${APP_ADMIN_NOTIFY_EMAIL:admin@badhabinot.com}")
    private String adminNotifyEmail;

    public MailServiceImpl(JavaMailSender mailSender, PasswordResetProperties properties) {
        this.mailSender = mailSender;
        this.properties = properties;
    }

    @Override
    public void sendPasswordResetEmail(String to, String token) {
        String resetUrl = properties.resetUrlTemplate().replace("{token}", token);

        SimpleMailMessage message = new SimpleMailMessage();
        message.setTo(to);
        message.setSubject("BADHABINOT – Şifre Sıfırlama");
        message.setText(
                "Merhaba,\n\n" +
                "Şifrenizi sıfırlamak için aşağıdaki bağlantıya tıklayın:\n\n" +
                resetUrl + "\n\n" +
                "Bu bağlantı 1 saat geçerlidir.\n\n" +
                "Bu isteği siz yapmadıysanız bu e-postayı görmezden gelebilirsiniz.\n\n" +
                "BADHABINOT"
        );

        try {
            mailSender.send(message);
            log.info("Password reset email sent to {}", to);
        } catch (MailException e) {
            log.error("Failed to send password reset email to {}: {}", to, e.getMessage());
        }
    }

    @Override
    public void sendNewUserNotification(String newUserEmail) {
        SimpleMailMessage message = new SimpleMailMessage();
        message.setTo(adminNotifyEmail);
        message.setSubject("BADHABINOT – Yeni kullanıcı onay bekliyor");
        message.setText(
                "Yeni bir kullanıcı kaydoldu ve onayınızı bekliyor:\n\n" +
                newUserEmail + "\n\n" +
                "Yönetim panelinden onaylayabilirsiniz.\n\n" +
                "BADHABINOT"
        );
        try {
            mailSender.send(message);
            log.info("New-user notification sent to admin for {}", newUserEmail);
        } catch (MailException e) {
            log.error("Failed to send new-user notification for {}: {}", newUserEmail, e.getMessage());
        }
    }
}
