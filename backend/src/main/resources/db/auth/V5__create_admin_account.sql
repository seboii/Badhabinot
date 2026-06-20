-- Sabit admin hesabi: admin@badhabinot.com / Admin123!
-- password_hash, uygulamanin BCryptPasswordEncoder'i (strength 10) ile uretildi.
-- Profil/ayar/onay kayitlari ilk kullanici-baglamı erisiminde otomatik olusur (lazy bootstrap).
-- Mevcut deploy'da hesap zaten varsa rol/sifre guncellenir (idempotent).
INSERT INTO auth_users (id, email, password_hash, role, status, created_at, updated_at)
VALUES (
    'f13f964d-a905-46b9-acb2-f12de256f1ac',
    'admin@badhabinot.com',
    '$2a$10$c3itECew9wgYzYAc5inzbeRwq9jXZYNvzdGGW1Rbfq6ozmyK1q7YK',
    'ADMIN',
    'ACTIVE',
    now(),
    now()
)
ON CONFLICT (email) DO UPDATE
    SET role = 'ADMIN',
        password_hash = EXCLUDED.password_hash,
        updated_at = now();
