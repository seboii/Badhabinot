package com.badhabinot.backend.infrastructure.redis;

import com.badhabinot.backend.common.exception.auth.InvalidCaptchaException;
import com.badhabinot.backend.dto.auth.CaptchaChallengeResponse;
import java.awt.BasicStroke;
import java.awt.Color;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.geom.Ellipse2D;
import java.awt.geom.Path2D;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Base64;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ThreadLocalRandom;
import java.util.stream.Collectors;
import javax.imageio.ImageIO;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

/**
 * Sunucu-taraflı görsel CAPTCHA — harici servis gerektirmez.
 *
 * <p>Akış:
 * <ol>
 *   <li>{@link #issue()} 3×3 ızgarada 9 karo üretir; her karo sunucuda PNG'ye
 *       çizilir (şekil bilgisi JSON'da DEĞİL, yalnızca piksel olarak gönderilir →
 *       bir bot çözmek için görüntü tanıma yapmak zorunda). Doğru indeksler
 *       Redis'te saklanır.</li>
 *   <li>{@link #verify(String, List)} kullanıcı seçimini sunucuda doğrular, doğruysa
 *       tek-kullanımlık bir "geçiş token'ı" üretip Redis'e yazar (challenge tüketilir).</li>
 *   <li>{@link #consumePass(String)} kayıt anında token'ı tüketir; yoksa reddeder.</li>
 * </ol>
 *
 * <p>Güvenlik gerekçesi: istemci-taraflı captcha bileşeni doğrudan API çağrısıyla
 * atlanabilir. Burada doğrulama kaynağı sunucudur; istemcinin gönderdiği "geçtim"
 * bilgisine güvenilmez. Redis erişilemezse <b>fail-open</b> davranır (IP-bazlı kayıt
 * rate-limit'i birincil savunma olarak kalır) — proje ilkesi "Redis kaybı kabul
 * edilebilir" ile uyumlu.
 */
@Service
public class CaptchaService {

    private static final Logger log = LoggerFactory.getLogger(CaptchaService.class);

    private static final String CHALLENGE_PREFIX = "captcha:challenge:";
    private static final String PASS_PREFIX = "captcha:pass:";
    private static final Duration TTL = Duration.ofMinutes(10);
    private static final int GRID = 9;
    private static final int TILE_PX = 72;

    /** Desteklenen şekiller — TR/EN etiketleriyle. */
    private enum Shape {
        CIRCLE("daire", "circle"),
        SQUARE("kare", "square"),
        TRIANGLE("üçgen", "triangle"),
        DIAMOND("baklava", "diamond"),
        STAR("yıldız", "star");

        final String tr;
        final String en;

        Shape(String tr, String en) {
            this.tr = tr;
            this.en = en;
        }
    }

    private static final Color[] PALETTE = {
        new Color(0x6366f1), new Color(0xec4899), new Color(0x14b8a6),
        new Color(0xf59e0b), new Color(0x22c55e), new Color(0xef4444),
        new Color(0x8b5cf6), new Color(0x0ea5e9), new Color(0xf97316),
    };

    private final StringRedisTemplate redisTemplate;

    public CaptchaService(StringRedisTemplate redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    /** Yeni bir captcha challenge üretir ve doğru indeksleri Redis'e yazar. */
    public CaptchaChallengeResponse issue() {
        ThreadLocalRandom rnd = ThreadLocalRandom.current();
        Shape[] all = Shape.values();
        Shape target = all[rnd.nextInt(all.length)];

        int correctCount = 3 + rnd.nextInt(2); // 3 veya 4 doğru karo
        List<Integer> positions = new ArrayList<>();
        for (int i = 0; i < GRID; i++) {
            positions.add(i);
        }
        Collections.shuffle(positions, ThreadLocalRandom.current());
        Set<Integer> correct = new HashSet<>(positions.subList(0, correctCount));

        List<String> tiles = new ArrayList<>(GRID);
        for (int i = 0; i < GRID; i++) {
            Shape shape = correct.contains(i)
                    ? target
                    : nonTarget(target, rnd);
            Color color = PALETTE[rnd.nextInt(PALETTE.length)];
            tiles.add(renderTile(shape, color));
        }

        String captchaId = UUID.randomUUID().toString();
        String correctCsv = correct.stream().sorted().map(String::valueOf).collect(Collectors.joining(","));
        try {
            redisTemplate.opsForValue().set(CHALLENGE_PREFIX + captchaId, correctCsv, TTL);
        } catch (Exception e) {
            log.warn("Captcha challenge Redis'e yazilamadi: {}", e.getMessage());
        }

        return new CaptchaChallengeResponse(captchaId, target.tr, target.en, tiles);
    }

    /**
     * Kullanıcı seçimini doğrular. Doğruysa challenge'ı tüketip tek-kullanımlık bir
     * geçiş token'ı döndürür; yanlış/expired ise {@link InvalidCaptchaException} fırlatır.
     */
    public String verify(String captchaId, List<Integer> answer) {
        if (captchaId == null || captchaId.isBlank()) {
            throw new InvalidCaptchaException("Doğrulama bulunamadı, lütfen yenileyin.");
        }
        String key = CHALLENGE_PREFIX + captchaId;
        String correctCsv;
        try {
            correctCsv = redisTemplate.opsForValue().get(key);
            redisTemplate.delete(key); // tek-kullanım: başarı/başarısızlık fark etmez
        } catch (Exception e) {
            log.warn("Captcha verify Redis hatasi, fail-open: {}", e.getMessage());
            return issuePass(); // Redis yoksa kayıt akışını bloklamayalım (rate-limit korur)
        }
        if (correctCsv == null) {
            throw new InvalidCaptchaException("Doğrulama süresi doldu, lütfen yenileyin.");
        }

        Set<Integer> correct = parseCsv(correctCsv);
        Set<Integer> given = answer == null ? Set.of() : new HashSet<>(answer);
        if (!correct.equals(given)) {
            throw new InvalidCaptchaException("Doğrulama hatalı, lütfen tekrar deneyin.");
        }
        return issuePass();
    }

    /**
     * Kayıt anında geçiş token'ını tüketir. Token yok/expired ise reddeder.
     * Redis hatasında fail-open (true).
     */
    public void consumePass(String token) {
        if (token == null || token.isBlank()) {
            throw new InvalidCaptchaException("Robot doğrulaması gerekli.");
        }
        try {
            Boolean removed = redisTemplate.delete(PASS_PREFIX + token);
            if (Boolean.FALSE.equals(removed)) {
                throw new InvalidCaptchaException("Robot doğrulaması süresi doldu, lütfen tekrar doğrulayın.");
            }
        } catch (InvalidCaptchaException e) {
            throw e;
        } catch (Exception e) {
            log.warn("Captcha pass Redis hatasi, fail-open: {}", e.getMessage());
        }
    }

    // ── yardımcılar ──────────────────────────────────────────────────────────

    private String issuePass() {
        String token = UUID.randomUUID().toString();
        try {
            redisTemplate.opsForValue().set(PASS_PREFIX + token, "1", TTL);
        } catch (Exception e) {
            log.warn("Captcha pass token yazilamadi: {}", e.getMessage());
        }
        return token;
    }

    private static Shape nonTarget(Shape target, ThreadLocalRandom rnd) {
        Shape[] all = Shape.values();
        Shape s;
        do {
            s = all[rnd.nextInt(all.length)];
        } while (s == target);
        return s;
    }

    private static Set<Integer> parseCsv(String csv) {
        Set<Integer> out = new HashSet<>();
        for (String part : csv.split(",")) {
            if (!part.isBlank()) {
                out.add(Integer.parseInt(part.trim()));
            }
        }
        return out;
    }

    /** Bir şekli renkli olarak küçük PNG'ye çizer ve {@code data:image/png;base64,...} döndürür. */
    private static String renderTile(Shape shape, Color color) {
        BufferedImage img = new BufferedImage(TILE_PX, TILE_PX, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = img.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        // Koyu yumuşak arka plan (frontend yüzeyiyle uyumlu)
        g.setColor(new Color(0x1f2433));
        g.fillRoundRect(0, 0, TILE_PX, TILE_PX, 14, 14);
        g.setColor(color);
        g.setStroke(new BasicStroke(2f));

        int cx = TILE_PX / 2;
        int cy = TILE_PX / 2;
        int r = 22;
        switch (shape) {
            case CIRCLE -> g.fill(new Ellipse2D.Double(cx - r, cy - r, r * 2.0, r * 2.0));
            case SQUARE -> g.fillRoundRect(cx - r, cy - r, r * 2, r * 2, 6, 6);
            case TRIANGLE -> g.fill(polygon(new int[]{cx, cx + r, cx - r}, new int[]{cy - r, cy + r, cy + r}));
            case DIAMOND -> g.fill(polygon(new int[]{cx, cx + r, cx, cx - r}, new int[]{cy - r, cy, cy + r, cy}));
            case STAR -> g.fill(star(cx, cy, r, r * 0.45));
        }
        g.dispose();

        try {
            ByteArrayOutputStream baos = new ByteArrayOutputStream();
            ImageIO.write(img, "png", baos);
            return "data:image/png;base64," + Base64.getEncoder().encodeToString(baos.toByteArray());
        } catch (IOException e) {
            // Pratikte ByteArrayOutputStream IOException atmaz; yine de güvenli dön.
            log.warn("Captcha tile render hatasi: {}", e.getMessage());
            return "";
        }
    }

    private static Path2D polygon(int[] xs, int[] ys) {
        Path2D path = new Path2D.Double();
        path.moveTo(xs[0], ys[0]);
        for (int i = 1; i < xs.length; i++) {
            path.lineTo(xs[i], ys[i]);
        }
        path.closePath();
        return path;
    }

    private static Path2D star(int cx, int cy, double outerR, double innerR) {
        Path2D path = new Path2D.Double();
        int points = 5;
        for (int i = 0; i < points * 2; i++) {
            double angle = (Math.PI / points) * i - Math.PI / 2;
            double rad = (i % 2 == 0) ? outerR : innerR;
            double x = cx + rad * Math.cos(angle);
            double y = cy + rad * Math.sin(angle);
            if (i == 0) {
                path.moveTo(x, y);
            } else {
                path.lineTo(x, y);
            }
        }
        path.closePath();
        return path;
    }
}
