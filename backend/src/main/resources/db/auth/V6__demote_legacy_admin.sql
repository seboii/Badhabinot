-- Eski yer-tutucu admin (tashkent0406@gmail.com) artik normal kullanici olsun.
-- V4 bu hesabi ADMIN yapmisti; tek kanonik admin admin@badhabinot.com (V5).
UPDATE auth_users
SET role = 'USER', updated_at = now()
WHERE LOWER(email) = LOWER('tashkent0406@gmail.com');
