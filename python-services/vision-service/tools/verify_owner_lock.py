"""Canli cok-kisili owner-lock dogrulayici.

Faz A+B'nin gercek karelerde calistigini KANITLAR: bir kullanicinin yuzu kayitli
oldugunda, kamerada baska yuzler de olsa SADECE o kullanici analiz edilmeli.

Birim testler mantigi kanitlar; bu arac gercek MediaPipe/YOLO/DeepFace'in gercek
goruntude sahibe kilitlendigini gosterir. Vision servisini DOGRUDAN cagirir
(owner-lock mantiginin yasadigi katman).

ON KOSULLAR
-----------
1. Vision servisi calisiyor olmali:  make local-up   (ya da uvicorn app.main:app --port 8091)
2. INTERNAL_API_KEY ortam degiskeni (ya da --api-key) backend'inkiyle ayni olmali.
3. Test goruntuleri (gercekten senin yuzunu icermeli — tamamen sentetik olmaz).
   Yoksa --capture ile webcam'den cek.

KULLANIM
--------
# (istege bagli) webcam'den kare yakala:
python -m tools.verify_owner_lock --capture data/verify_shots --shots 6

# kayit + senaryolari kos:
python -m tools.verify_owner_lock \
    --owner data/verify_shots/owner_1.jpg data/verify_shots/owner_2.jpg data/verify_shots/owner_3.jpg \
    --owner-solo data/verify_shots/solo.jpg \
    --owner-with-stranger data/verify_shots/with_friend.jpg \
    --stranger-only data/verify_shots/friend_only.jpg

Cikis kodu: tum senaryolar gecerse 0, aksi halde 1.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

_DEFAULT_BASE = os.getenv("VISION_SERVICE_URL", "http://localhost:8091")
_DEFAULT_KEY = os.getenv("INTERNAL_API_KEY", "change-me-in-real-environments")
# vision behavior_engine'in sahip-yoklugu/yabanci olaylari
_ABSENCE_EVENTS = {"OWNER_ABSENT", "STRANGER_DETECTED", "UNKNOWN_PERSON"}


# ── HTTP (stdlib — ek bagimlilik yok) ───────────────────────────────────────
def _http(method: str, url: str, api_key: str, payload: dict | None = None, timeout: float = 40.0) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"X-Internal-Api-Key": api_key}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise SystemExit(f"HTTP {exc.code} {method} {url}\n  {detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(
            f"Vision servisine ulasilamadi ({url}): {exc.reason}\n"
            "  -> servis calisiyor mu? 'make local-up' veya uvicorn ile baslat."
        ) from exc


def _encode_image(path: str) -> tuple[str, str]:
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"Goruntu bulunamadi: {path}")
    raw = p.read_bytes()
    ct = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
    return base64.b64encode(raw).decode("ascii"), ct


# ── Vision API sarmalayicilari ──────────────────────────────────────────────
def delete_profile(base: str, key: str, user_id: str) -> None:
    res = _http("DELETE", f"{base}/v1/vision/face/{user_id}", key)
    print(f"  temizlik: profil silindi={res.get('deleted')}")


def register_owner(base: str, key: str, user_id: str, images: list[str]) -> int:
    frames = 0
    for img in images:
        b64, ct = _encode_image(img)
        res = _http("POST", f"{base}/v1/vision/face/register", key, {
            "user_id": user_id, "image_base64": b64, "image_content_type": ct,
        })
        frames = res.get("frames_enrolled", frames)
        ok = res.get("success")
        print(f"  kayit: {Path(img).name} -> success={ok} frames={frames} ({res.get('message','')})")
    return frames


def get_status(base: str, key: str, user_id: str) -> dict:
    return _http("GET", f"{base}/v1/vision/face/{user_id}/status", key)


def analyze_frame(base: str, key: str, user_id: str, image: str) -> dict:
    b64, ct = _encode_image(image)
    return _http("POST", f"{base}/v1/vision/analyze", key, {
        "request_id": str(uuid.uuid4()),
        "user_id": user_id,
        "session_id": "verify-owner-lock",
        "frame_id": str(uuid.uuid4()),
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "image_base64": b64,
        "image_content_type": ct,
    })


# ── Senaryo degerlendirme ───────────────────────────────────────────────────
def _summarize(resp: dict) -> str:
    auth = resp.get("auth") or {}
    owner = resp.get("owner_tracking") or {}
    events = [e.get("event_type") for e in (resp.get("behavior_events") or [])]
    dets = [d.get("event_type") for d in (resp.get("detections") or [])]
    pose = resp.get("pose") or {}
    mesh = resp.get("face_mesh") or {}
    return (
        f"auth(authenticated={auth.get('authenticated')}, conf={auth.get('confidence')}) "
        f"owner(tracked={owner.get('owner_tracked')}, strangers={owner.get('strangers_in_frame')}) "
        f"posture_state={resp.get('posture_state')} pose_score={pose.get('posture_score')} "
        f"drowsy={mesh.get('is_drowsy')} yawning={mesh.get('is_yawning')} "
        f"detections={dets} events={events}"
    )


def _check(name: str, ok: bool, resp: dict) -> bool:
    tag = "[PASS]" if ok else "[FAIL]"
    print(f"\n{tag} {name}")
    print(f"       {_summarize(resp)}")
    return ok


def run_scenarios(base: str, key: str, user_id: str, args: argparse.Namespace) -> bool:
    results: list[bool] = []

    if args.owner_solo:
        r = analyze_frame(base, key, user_id, args.owner_solo)
        owner = r.get("owner_tracking") or {}
        ok = bool(owner.get("owner_tracked")) and (owner.get("strangers_in_frame") or 0) == 0
        results.append(_check("Sahip yalniz -> owner_tracked=True, strangers=0", ok, r))

    if args.owner_with_stranger:
        r = analyze_frame(base, key, user_id, args.owner_with_stranger)
        owner = r.get("owner_tracking") or {}
        ok = bool(owner.get("owner_tracked")) and (owner.get("strangers_in_frame") or 0) >= 1
        results.append(_check(
            "Sahip + yabanci -> owner_tracked=True, strangers>=1 (sahip kilitli, yabanci sayildi)",
            ok, r,
        ))

    if args.stranger_only:
        r = analyze_frame(base, key, user_id, args.stranger_only)
        owner = r.get("owner_tracking") or {}
        events = {e.get("event_type") for e in (r.get("behavior_events") or [])}
        # Anlik + guvenilir sinyal: sahip kilitlenmedi ve yabanci sayildi.
        # (OWNER_ABSENT/STRANGER olayi sure-tabanli olabilir; bilgi amacli yazdirilir.)
        ok = (not owner.get("owner_tracked")) and (owner.get("strangers_in_frame") or 0) >= 1
        absence_evt = "var" if (events & _ABSENCE_EVENTS) else "yok (sure-tabanli olabilir)"
        results.append(_check(
            f"Yalniz yabanci -> owner_tracked=False, strangers>=1 (atfetme yok) | absence olayi: {absence_evt}",
            ok, r,
        ))

    if not results:
        print("\nUyari: hicbir senaryo verilmedi (--owner-solo / --owner-with-stranger / --stranger-only).")
        return False

    passed = sum(results)
    print(f"\n=== Sonuc: {passed}/{len(results)} senaryo gecti ===")
    return passed == len(results)


# ── Webcam yakalama (istege bagli yardimci) ─────────────────────────────────
def capture_webcam(out_dir: str, shots: int) -> None:
    import cv2  # noqa: PLC0415 — yalnizca --capture icin

    Path(out_dir).mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise SystemExit("Webcam acilamadi (index 0).")
    print(f"Yakalama: SPACE=kaydet, q=cik. Hedef klasor: {out_dir}")
    count = 0
    while count < shots:
        ok, frame = cap.read()
        if not ok:
            break
        cv2.imshow("verify_owner_lock — SPACE kaydet / q cik", frame)
        keyp = cv2.waitKey(1) & 0xFF
        if keyp == ord(" "):
            path = Path(out_dir) / f"shot_{count:02d}.jpg"
            cv2.imwrite(str(path), frame)
            print(f"  kaydedildi: {path}")
            count += 1
        elif keyp == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()
    print(f"Toplam {count} kare yakalandi -> {out_dir}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Owner-lock canli dogrulayici")
    ap.add_argument("--base-url", default=_DEFAULT_BASE)
    ap.add_argument("--api-key", default=_DEFAULT_KEY)
    ap.add_argument("--user-id", default="owner-verify")
    ap.add_argument("--owner", nargs="+", help="Kayit icin sahip yuzu goruntuleri (3+)")
    ap.add_argument("--owner-solo", help="Senaryo: sahip yalniz")
    ap.add_argument("--owner-with-stranger", help="Senaryo: sahip + yabanci")
    ap.add_argument("--stranger-only", help="Senaryo: yalniz yabanci")
    ap.add_argument("--keep-profile", action="store_true", help="Bitiste profili silme")
    ap.add_argument("--capture", metavar="DIR", help="Webcam'den kare yakala ve cik")
    ap.add_argument("--shots", type=int, default=6, help="--capture icin kare sayisi")
    args = ap.parse_args(argv)

    if args.capture:
        capture_webcam(args.capture, args.shots)
        return 0

    base, key, user_id = args.base_url.rstrip("/"), args.api_key, args.user_id
    print(f"Vision: {base} | user_id: {user_id}")

    if args.owner:
        print("\n[1] Sahip yuzu kaydi")
        delete_profile(base, key, user_id)
        frames = register_owner(base, key, user_id, args.owner)
        if frames < 3:
            print(f"  UYARI: yalnizca {frames} kare - profil aktif degil (3+ farkli kare gerekir).")
        st = get_status(base, key, user_id)
        print(f"  durum: active={st.get('success')} frames={st.get('frames_enrolled')}")
    else:
        print("\n[1] Kayit atlandi (--owner verilmedi) - mevcut profil kullanilacak.")

    print("\n[2] Senaryolar")
    all_pass = run_scenarios(base, key, user_id, args)

    if args.owner and not args.keep_profile:
        print("\n[3] Temizlik")
        delete_profile(base, key, user_id)

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
