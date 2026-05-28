"""Faz 1 — Behavioral detection değerlendirme harness'ı.

Bu paket, davranış tespiti pipeline'ının doğruluğunu etiketli bir veri seti
üzerinde ölçer: confusion matrix, precision / recall / F1. Tezin "Deneysel
Sonuçlar" bölümünün temelini ve mevcut heuristiklerin baseline'ını üretir.

Bağımsız çalışır — metrics modülü ML kütüphanesi gerektirmez (saf numpy),
böylece CI'da ve veri olmadan da test edilebilir.
"""
