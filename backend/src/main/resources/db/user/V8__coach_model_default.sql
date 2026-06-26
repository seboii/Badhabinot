-- Sohbet tek modele indirildi: artık yalnızca fine-tune edilmiş koç modeli kullanılır.
-- Varsayılan yerel model qwen7b-tabanlı 'badhabinot:latest' yerine 'badhabinot-coach:latest'.
-- qwen wrapper'ı kullanan mevcut kayıtlar fine-tune modeline taşınır.
UPDATE user_settings
SET local_model_name = 'badhabinot-coach:latest'
WHERE local_model_name = 'badhabinot:latest' OR local_model_name IS NULL;
