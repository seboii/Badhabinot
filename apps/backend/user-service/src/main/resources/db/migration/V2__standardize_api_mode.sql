UPDATE user_settings
SET model_mode = 'API'
WHERE model_mode IS NULL OR model_mode <> 'API';
