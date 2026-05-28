-- Sohbet personası ve özelleştirilebilir system prompt.
-- GENERAL_CHAT  → doğal sohbet (varsayılan), monitoring verisi sadece sorulduğunda
-- BEHAVIOR_COACH → mevcut davranış koçluğu (monitoring verisi her zaman bağlı)
-- CUSTOM         → kullanıcı kendi system prompt'unu sağlar
ALTER TABLE user_settings
    ADD COLUMN chat_persona VARCHAR(32) NOT NULL DEFAULT 'GENERAL_CHAT';

ALTER TABLE user_settings
    ADD COLUMN custom_system_prompt TEXT;

-- Mevcut kayıtlar genel sohbete geçirilir (kullanıcı isterse Settings'ten değiştirir).
UPDATE user_settings SET chat_persona = 'GENERAL_CHAT' WHERE chat_persona IS NULL;
