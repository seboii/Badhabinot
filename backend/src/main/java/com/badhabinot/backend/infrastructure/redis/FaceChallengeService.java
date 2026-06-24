package com.badhabinot.backend.infrastructure.redis;

import com.badhabinot.backend.common.exception.auth.FaceLivenessFailedException;
import com.badhabinot.backend.dto.auth.FaceChallengeResponse;
import java.time.Duration;
import java.util.UUID;
import java.util.concurrent.ThreadLocalRandom;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

/**
 * Yüz girişi canlılık (liveness) challenge'ı için Redis tabanlı tek-kullanımlık store.
 *
 * <p>{@link #issue()} rastgele bir eylem (BLINK/TURN_HEAD) seçip Redis'e yazar ve
 * istemciye gönderir. {@link #consume(String)} kayıt anında challenge'ı tüketip
 * eylemi döndürür. Challenge tek-kullanımlık ve kısa ömürlüdür → istemci önceden
 * kaydedilmiş bir video ile geçmeye çalışamaz.
 *
 * <p>Bir GÜVENLİK kontrolü olduğundan Redis erişilemezse <b>fail-closed</b>
 * davranır (yüz girişi reddedilir; kullanıcı şifre ile girebilir).
 */
@Service
public class FaceChallengeService {

    private static final Logger log = LoggerFactory.getLogger(FaceChallengeService.class);
    private static final String PREFIX = "face-challenge:";
    private static final Duration TTL = Duration.ofMinutes(2);
    private static final String[] ACTIONS = {"BLINK", "TURN_HEAD"};

    private final StringRedisTemplate redisTemplate;

    public FaceChallengeService(StringRedisTemplate redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    public FaceChallengeResponse issue() {
        String action = ACTIONS[ThreadLocalRandom.current().nextInt(ACTIONS.length)];
        String challengeId = UUID.randomUUID().toString();
        try {
            redisTemplate.opsForValue().set(PREFIX + challengeId, action, TTL);
        } catch (Exception e) {
            log.warn("Face challenge Redis'e yazilamadi: {}", e.getMessage());
            throw new FaceLivenessFailedException("Doğrulama servisi şu an kullanılamıyor, lütfen şifre ile giriş yapın.");
        }
        return new FaceChallengeResponse(challengeId, action, promptTr(action), promptEn(action));
    }

    /** Challenge'ı tüketip istenen eylemi döndürür; yoksa/expired ise reddeder. */
    public String consume(String challengeId) {
        if (challengeId == null || challengeId.isBlank()) {
            throw new FaceLivenessFailedException("Doğrulama görevi bulunamadı, lütfen tekrar deneyin.");
        }
        String action;
        try {
            String key = PREFIX + challengeId;
            action = redisTemplate.opsForValue().get(key);
            redisTemplate.delete(key); // tek-kullanım
        } catch (Exception e) {
            log.warn("Face challenge Redis hatasi: {}", e.getMessage());
            throw new FaceLivenessFailedException("Doğrulama servisi şu an kullanılamıyor, lütfen şifre ile giriş yapın.");
        }
        if (action == null) {
            throw new FaceLivenessFailedException("Doğrulama görevi süresi doldu, lütfen tekrar deneyin.");
        }
        return action;
    }

    private static String promptTr(String action) {
        return "BLINK".equals(action) ? "Gözlerinizi kırpın" : "Başınızı hafifçe sağa veya sola çevirin";
    }

    private static String promptEn(String action) {
        return "BLINK".equals(action) ? "Blink your eyes" : "Turn your head left or right";
    }
}
