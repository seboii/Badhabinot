"""Faz 2 — Landmark-tabanlı davranış sınıflandırma (eğitim iskeleti).

Heuristik eşiklerin yerine, vision pipeline'ının ürettiği landmark + türev
özelliklerden öğrenen bir temporal model eğitir. Davranış tek karede değil bir
hareket dizisinde belirir; bu yüzden model bir kare penceresi (window) üzerinde
çalışır.

Tasarım:
- landmark_features.py — saf numpy özellik çıkarımı (ML bağımlılığı yok, test edilebilir)
- model.py / sequence_dataset.py / train.py / infer.py — PyTorch (requirements-train.txt)
- collect.py — webcam'den landmark dizisi toplama

Gizlilik: özellikler landmark koordinatları + türevlerdir; ham görüntü modele girmez.
"""
