"""Persistance simple : la liste des annonces déjà vues, dans un fichier JSON.

Pourquoi un JSON et pas une base SQLite ? Parce que le scraper tourne sur
GitHub Actions, qui repart d'un environnement vierge à chaque exécution. Un
fichier JSON commité dans le dépôt persiste entre les runs et reste lisible.
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

from config import (
    RECENT_PATH,
    RECENT_RETENTION_HOURS,
    SEEN_IDS_PATH,
    TOP5_MAX_AGE_DAYS,
    TOP5_PATH,
)


def load_seen_ids(path: Path = SEEN_IDS_PATH) -> set[str]:
    """Retourne l'ensemble des IDs d'annonces déjà vues.

    On utilise un set (et pas une liste) car le test « est-ce déjà vu ? »
    est instantané sur un set, peu importe le nombre d'éléments.
    """
    if not path.exists():
        return set()
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return set(data.get("ids", []))


def save_seen_ids(ids: set[str], path: Path = SEEN_IDS_PATH) -> None:
    """Écrit l'ensemble des IDs vus, trié pour un diff git propre."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "ids": sorted(ids),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_recent(path: Path = RECENT_PATH) -> list[dict]:
    """Charge les annonces récentes (pour le récap quotidien)."""
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def add_recent(new_listings: list[dict], path: Path = RECENT_PATH) -> None:
    """Ajoute des annonces au fichier récent et purge celles de +48h.

    Chaque annonce reçoit un champ `seen_at` (horodatage UTC) au moment où on
    la voit pour la première fois. recap.py s'en sert pour ne garder que les
    dernières 24h.
    """
    now = datetime.now(timezone.utc)
    stamped = []
    for l in new_listings:
        entry = dict(l)
        entry["seen_at"] = now.isoformat()
        stamped.append(entry)

    existing = load_recent(path)
    combined = existing + stamped

    # Purge : on retire les annonces trop vieilles pour garder le fichier petit.
    cutoff = now - timedelta(hours=RECENT_RETENTION_HOURS)
    kept = []
    for l in combined:
        try:
            seen = datetime.fromisoformat(l["seen_at"])
        except (KeyError, ValueError):
            continue  # entrée malformée → on la jette
        if seen >= cutoff:
            kept.append(l)

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(kept, f, ensure_ascii=False, indent=2)


# --- Top 5 ---

def load_top5(path: Path = TOP5_PATH) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_top5(top5: list[dict], path: Path = TOP5_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(top5, f, ensure_ascii=False, indent=2)


def is_listing_online(url: str) -> bool:
    """Retourne True si l'annonce est encore accessible. Fail-safe : True en cas d'erreur."""
    try:
        resp = requests.get(
            url, timeout=10, allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
        )
        return resp.status_code == 200 and "not-found" not in resp.url
    except Exception:
        return True


def update_top5(new_kept: list[dict], dry_run: bool = False) -> None:
    """Met à jour le top 5 : retire les annonces hors ligne ou expirées, ajoute les nouvelles, garde les 5 meilleurs scores."""
    top5 = load_top5()
    now = datetime.now(timezone.utc)

    # Vérifier que les entrées actuelles sont encore en ligne et pas trop vieilles.
    # Une annonce reste au max TOP5_MAX_AGE_DAYS dans le top5, même si elle est
    # toujours en ligne et bien notée : évite qu'un vélo "correct mais jamais
    # acheté" y reste indéfiniment.
    still_online = []
    for l in top5:
        # `added_at` absent (fichier existant avant l'ajout de ce champ) :
        # on considère l'entrée comme fraîche plutôt que de vider le top5 d'un coup.
        added_at = l.get("added_at") or now.isoformat()
        l = {**l, "added_at": added_at}

        age_days = (now - datetime.fromisoformat(added_at)).days
        if age_days >= TOP5_MAX_AGE_DAYS:
            print(f"  [top5] retirée (expirée après {TOP5_MAX_AGE_DAYS}j) : {l['title']}")
        elif is_listing_online(l["url"]):
            still_online.append(l)
        else:
            print(f"  [top5] retirée (hors ligne) : {l['title']}")

    # Ajouter les nouvelles candidates retenues par l'IA
    existing_ids = {l["id"] for l in still_online}
    for l in new_kept:
        if l["id"] not in existing_ids:
            analyse = l.get("_analyse") or {}
            still_online.append({
                "id": l["id"],
                "title": l.get("title", ""),
                "price_raw": l.get("price_raw", ""),
                "location": l.get("location", ""),
                "url": l.get("url", ""),
                "posted_at": l.get("posted_at", ""),
                "score": analyse.get("score", 0),
                "raison": analyse.get("raison", ""),
                "conseil": analyse.get("conseil", ""),
                "added_at": now.isoformat(),
            })

    still_online.sort(key=lambda x: x.get("score", 0), reverse=True)
    new_top5 = still_online[:5]

    if not dry_run:
        save_top5(new_top5)

    print(f"\n{'[DRY-RUN] ' if dry_run else ''}Top 5 meilleures annonces en ligne :")
    for i, l in enumerate(new_top5, 1):
        print(f"  {i}. [{l.get('score', '?')}/100] {l['title']} — {l.get('price_raw', '?')}")
        if l.get("conseil"):
            print(f"     💡 {l['conseil']}")
