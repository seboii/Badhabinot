-- Admin rolü tohumlama (gerçek hesap).
-- V3 yer tutucu bir e-posta ile yazılmıştı; uygulamada kayıtlı gerçek hesabı
-- ADMIN yapıyoruz. Flyway uygulanmış migration'lar düzenlenemediği için yeni
-- bir migration olarak eklenir. Farklı bir admin istersen aşağıdaki adresi
-- güncelle (veya yeni bir V5 migration ekle).
UPDATE auth_users
SET role = 'ADMIN', updated_at = now()
WHERE LOWER(email) = LOWER('tashkent0406@gmail.com');
