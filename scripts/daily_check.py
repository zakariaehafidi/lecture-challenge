#!/usr/bin/env python3
"""Vérification quotidienne : attribue un challenge à chaque personne qui n'a pas
validé ses 20 pages la veille (heure de Paris), puis l'envoie par WhatsApp
(CallMeBot) ou, à défaut, par email.

Uniquement la bibliothèque standard Python : aucune installation nécessaire.
"""
import base64
import copy
import json
import os
import random
import smtplib
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from email.message import EmailMessage
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Paris")
STATE_PATH = "data/state.json"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHALLENGES_FILE = os.path.join(ROOT, "data", "challenges.json")
MAX_CATCHUP_DAYS = 7  # au-delà, les jours manqués (ex. Action désactivée) sont ignorés
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
        "août", "septembre", "octobre", "novembre", "décembre"]


class Conflict(Exception):
    pass


# ---------------------------------------------------------------- logique pure

def today_paris():
    return datetime.now(TZ).date()


def pick_challenge(state, challenges, person_id, rng):
    """Choisit un challenge au hasard parmi ceux que la personne a eus le moins
    souvent : pas de répétition tant que toute la liste n'a pas été faite."""
    counts = {c["id"]: 0 for c in challenges}
    for entry in state["challenges"]:
        if entry["person"] == person_id and entry["challengeId"] in counts:
            counts[entry["challengeId"]] += 1
    lowest = min(counts.values())
    candidates = [c for c in challenges if counts[c["id"]] == lowest]
    return rng.choice(candidates)


def process_state(state, challenges, today, rng):
    """Renvoie (nouvel_état, nouvelles_attributions). Ne modifie pas l'entrée."""
    state = copy.deepcopy(state)
    state.setdefault("reading", {})
    state.setdefault("challenges", [])
    assignments = []

    if not state.get("startDate"):
        state["startDate"] = today.isoformat()
        return state, assignments

    start = date.fromisoformat(state["startDate"])
    last = state.get("lastProcessed")
    first = start if not last else date.fromisoformat(last) + timedelta(days=1)
    yesterday = today - timedelta(days=1)
    if first > yesterday:
        return state, assignments

    oldest_allowed = today - timedelta(days=MAX_CATCHUP_DAYS)
    now_iso = datetime.now(TZ).isoformat(timespec="seconds")
    d = first
    while d <= yesterday:
        if d >= oldest_allowed:
            ds = d.isoformat()
            done = state["reading"].get(ds, {})
            for person in state["people"]:
                if person["id"] in done:
                    continue
                ch = pick_challenge(state, challenges, person["id"], rng)
                entry = {
                    "id": f"{ds}-{person['id']}",
                    "date": ds,
                    "person": person["id"],
                    "challengeId": ch["id"],
                    "text": ch["text"],
                    "status": "pending",
                    "assignedAt": now_iso,
                    "validatedAt": None,
                    "validatedBy": None,
                }
                state["challenges"].append(entry)
                assignments.append(entry)
        d += timedelta(days=1)

    state["lastProcessed"] = yesterday.isoformat()
    return state, assignments


def format_date(ds):
    d = date.fromisoformat(ds)
    return f"{d.day} {MOIS[d.month - 1]}"


def build_message(entry, state, site_url):
    names = {p["id"]: p["name"] for p in state["people"]}
    name = names.get(entry["person"], entry["person"])
    others = [p["name"] for p in state["people"] if p["id"] != entry["person"]]
    other = others[0] if others else "l'autre"
    return (
        f"📚 Oups {name} ! Tes 20 pages du {format_date(entry['date'])} "
        f"n'ont pas été validées.\n\n"
        f"🎯 Ton challenge n°{entry['challengeId']} :\n{entry['text']}\n\n"
        f"🎥 Filme-toi et envoie la vidéo à {other}, qui le validera sur le site :\n"
        f"{site_url}"
    )


# ---------------------------------------------------------------- GitHub API

def _gh(method, url, body=None):
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "lecture-challenge",
    }
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code in (409, 422):
            raise Conflict(e.read().decode("utf-8", "replace"))
        raise RuntimeError(f"GitHub API {e.code} : {e.read().decode('utf-8', 'replace')}")


def _contents_url():
    repo = os.environ["GITHUB_REPOSITORY"]
    return f"https://api.github.com/repos/{repo}/contents/{STATE_PATH}"


def branch():
    return os.environ.get("GITHUB_REF_NAME") or "main"


def read_state():
    url = _contents_url() + "?ref=" + urllib.parse.quote(branch())
    j = _gh("GET", url)
    content = base64.b64decode(j["content"]).decode("utf-8")
    return json.loads(content), j["sha"]


def write_state(state, sha, message):
    text = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    _gh("PUT", _contents_url(), {
        "message": message,
        "content": base64.b64encode(text.encode("utf-8")).decode("ascii"),
        "sha": sha,
        "branch": branch(),
    })


# ---------------------------------------------------------------- envois

def env(name):
    return (os.environ.get(name) or "").strip()


def send_whatsapp(phone, apikey, text):
    url = "https://api.callmebot.com/whatsapp.php?" + urllib.parse.urlencode(
        {"phone": phone, "text": text, "apikey": apikey})
    req = urllib.request.Request(url, headers={"User-Agent": "lecture-challenge"})
    with urllib.request.urlopen(req, timeout=60) as res:
        body = res.read().decode("utf-8", "replace").lower()
        if res.status == 200 and ("queued" in body or "sent" in body):
            return
        raise RuntimeError(f"réponse inattendue de CallMeBot : {body[:200]}")


def send_email(to_addr, subject, text):
    user, password = env("GMAIL_USER"), env("GMAIL_APP_PASSWORD")
    if not user or not password:
        raise RuntimeError("GMAIL_USER / GMAIL_APP_PASSWORD manquants")
    msg = EmailMessage()
    msg["From"] = user
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(text)
    host = env("SMTP_HOST") or "smtp.gmail.com"
    port = int(env("SMTP_PORT") or "465")
    with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context(), timeout=60) as s:
        s.login(user, password.replace(" ", ""))
        s.send_message(msg)


def notify(person_id, subject, text):
    """WhatsApp d'abord, email en secours. Renvoie le canal utilisé ou None."""
    key = person_id.upper()
    phone, apikey, email = env(f"PHONE_{key}"), env(f"CALLMEBOT_KEY_{key}"), env(f"EMAIL_{key}")
    if phone and apikey:
        try:
            send_whatsapp(phone, apikey, text)
            print(f"  ✔ WhatsApp envoyé à {person_id}")
            return "whatsapp"
        except Exception as e:  # noqa: BLE001
            print(f"  ✘ WhatsApp échoué pour {person_id} : {e}")
    else:
        print(f"  · WhatsApp non configuré pour {person_id}")
    if email:
        try:
            send_email(email, subject, text)
            print(f"  ✔ Email envoyé à {person_id}")
            return "email"
        except Exception as e:  # noqa: BLE001
            print(f"  ✘ Email échoué pour {person_id} : {e}")
    else:
        print(f"  · Email non configuré pour {person_id}")
    return None


def site_url():
    if env("SITE_URL"):
        return env("SITE_URL")
    owner, repo = os.environ["GITHUB_REPOSITORY"].split("/", 1)
    host = f"{owner.lower()}.github.io"
    return f"https://{host}/" if repo.lower() == host else f"https://{host}/{repo}/"


# ---------------------------------------------------------------- main

def main():
    mode = env("MODE") or "normal"
    with open(CHALLENGES_FILE, encoding="utf-8") as f:
        challenges = json.load(f)
    rng = random.Random()
    today = today_paris()
    print(f"Date à Paris : {today.isoformat()} — mode : {mode}")

    if mode == "test-notifications":
        state, _ = read_state()
        failures = 0
        for p in state["people"]:
            text = (f"👋 Test de Lecture Challenge pour {p['name']} : si tu lis ce message, "
                    f"les notifications fonctionnent !\n{site_url()}")
            if not notify(p["id"], "Test Lecture Challenge", text):
                failures += 1
        sys.exit(1 if failures else 0)

    assignments = []
    for attempt in range(5):
        state, sha = read_state()
        new_state, assignments = process_state(state, challenges, today, rng)
        if new_state == state:
            print("Rien à faire aujourd'hui.")
            return
        try:
            write_state(new_state, sha, f"Vérification du {today.isoformat()}")
            state = new_state
            break
        except Conflict:
            print("Conflit d'écriture, nouvel essai…")
            time.sleep(2 * (attempt + 1))
    else:
        sys.exit("Impossible d'enregistrer l'état après 5 essais.")

    if not assignments:
        print("Tout le monde a lu. Bravo 🎉")
        return
    failures = 0
    for entry in assignments:
        print(f"Challenge {entry['challengeId']} → {entry['person']} ({entry['date']})")
        subject = f"📚 Ton challenge du {format_date(entry['date'])}"
        if not notify(entry["person"], subject, build_message(entry, state, site_url())):
            failures += 1
    if failures:
        sys.exit(f"{failures} notification(s) n'ont pas pu être envoyées (voir ci-dessus).")


if __name__ == "__main__":
    main()
