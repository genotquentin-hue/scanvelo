"""Envoi des notifications : Telegram (alertes instantanées) + email (récap).

On utilise l'API HTTP de Telegram directement via `requests` plutôt qu'une
librairie dédiée : un seul appel suffit, pas besoin d'une dépendance de plus.
"""
import smtplib
from email.message import EmailMessage
from html import escape

import requests

from config import (
    GMAIL_APP_PASSWORD,
    GMAIL_TO,
    GMAIL_USER,
    TELEGRAM_CHAT_ID,
    TELEGRAM_TOKEN,
)
from filters import distance_to_brussels, has_size_m

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


# --- Telegram : alertes instantanées ---

def send_telegram(listing: dict) -> bool:
    """Envoie une alerte Telegram pour une annonce. Retourne True si OK."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("  [warn] Telegram non configuré (token/chat_id manquants)")
        return False

    text = _format_telegram(listing)
    try:
        resp = requests.post(
            TELEGRAM_API.format(token=TELEGRAM_TOKEN),
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": False,
            },
            timeout=15,
        )
        resp.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"  [warn] échec envoi Telegram : {e}")
        return False


def _format_telegram(listing: dict) -> str:
    """Construit le message HTML d'une alerte. escape() neutralise les
    caractères spéciaux (<, >, &) pour ne pas casser le HTML Telegram."""
    title = escape(listing.get("title", "Sans titre"))
    price = escape(listing.get("price_raw", "?"))
    city = escape(listing.get("location") or "lieu inconnu")
    url = listing.get("url", "")

    dist = distance_to_brussels(listing)
    dist_str = f" (~{dist:.0f} km)" if dist is not None else ""
    size_str = "\n📏 Taille M mentionnée" if has_size_m(listing) else ""

    return (
        f"🚲 <b>Nouveau vélo</b>\n\n"
        f"🏷 {title}\n"
        f"💰 {price}\n"
        f"📍 {city}{dist_str}"
        f"{size_str}\n\n"
        f'🔗 <a href="{escape(url)}">Voir l\'annonce</a>'
    )


# --- Email : récap quotidien ---

def send_email_recap(listings: list[dict], subject: str | None = None) -> bool:
    """Envoie un récap par email via Gmail SMTP. Retourne True si OK."""
    if not GMAIL_USER or not GMAIL_APP_PASSWORD or not GMAIL_TO:
        print("  [warn] Gmail non configuré (user/app_password/to manquants)")
        return False

    if subject is None:
        subject = f"🚲 Récap vélos — {len(listings)} nouvelle(s) annonce(s)"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = GMAIL_TO
    msg.set_content(_format_email_text(listings))      # version texte (fallback)
    msg.add_alternative(_format_email_html(listings), subtype="html")

    try:
        # Port 465 = SMTP over SSL (connexion chiffrée d'emblée).
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        return True
    except (smtplib.SMTPException, OSError) as e:
        print(f"  [warn] échec envoi email : {e}")
        return False


def _format_email_text(listings: list[dict]) -> str:
    if not listings:
        return "Aucune nouvelle annonce dans les dernières 24h. Marché calme."
    lines = [f"{len(listings)} nouvelle(s) annonce(s) :\n"]
    for i, l in enumerate(listings, 1):
        city = l.get("location") or "?"
        lines.append(f"{i}. {l.get('title', '?')} — {l.get('price_raw', '?')} — {city}")
        lines.append(f"   {l.get('url', '')}\n")
    return "\n".join(lines)


def _format_email_html(listings: list[dict]) -> str:
    if not listings:
        return "<p>Aucune nouvelle annonce dans les dernières 24h. Marché calme. 🚲</p>"
    rows = []
    for l in listings:
        title = escape(l.get("title", "?"))
        price = escape(l.get("price_raw", "?"))
        city = escape(l.get("location") or "?")
        url = escape(l.get("url", ""))
        size = " · 📏 taille M" if has_size_m(l) else ""
        rows.append(
            f'<li style="margin-bottom:12px">'
            f'<a href="{url}"><b>{title}</b></a><br>'
            f"💰 {price} · 📍 {city}{size}"
            f"</li>"
        )
    return (
        f"<h2>🚲 {len(listings)} nouvelle(s) annonce(s)</h2>"
        f'<ul style="list-style:none;padding:0">{"".join(rows)}</ul>'
    )
