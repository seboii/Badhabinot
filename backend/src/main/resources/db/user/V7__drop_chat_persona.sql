-- Sohbet tek moda indirildi (davranış koçu): persona/özel-prompt mimarisi kaldırıldı.
-- V6'nın eklediği kolonlar düşürülür; tüm sohbet artık veriye-dayalı koç olarak çalışır.
ALTER TABLE user_settings DROP COLUMN IF EXISTS chat_persona;
ALTER TABLE user_settings DROP COLUMN IF EXISTS custom_system_prompt;
