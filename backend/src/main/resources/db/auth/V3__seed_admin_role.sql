-- Admin rolü tohumlama (tek e-posta).
-- Belirtilen e-postaya sahip kullanıcı ADMIN yapılır. Hesap bu migration
-- çalışmadan ÖNCE kayıtlı olmalıdır (aksi halde 0 satır etkilenir; o durumda
-- hesabı kaydedip yeni bir migration ile tekrar tohumlayın).
-- Admin e-postasını değiştirmek için aşağıdaki adresi güncelleyin.
UPDATE auth_users
SET role = 'ADMIN', updated_at = now()
WHERE LOWER(email) = LOWER('shakho0303@gmail.com');
