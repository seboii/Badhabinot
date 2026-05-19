package com.badhabinot.backend.service.auth;

import com.badhabinot.backend.config.PasswordResetProperties;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.MailException;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.stereotype.Service;

@Service
public class MailService {

    private static final Logger log = LoggerFactory.getLogger(MailService.class);

    private final JavaMailSender mailSender;
    private final PasswordResetProperties properties;

    public MailService(JavaMailSender mailSender, PasswordResetProperties properties) {
        this.mailSender = mailSender;
        this.properties = properties;
    }

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
}
