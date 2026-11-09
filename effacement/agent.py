#!/usr/bin/env python3
"""Agent d'effacement de données personnelles (RGPD, article 17).

Programme déterministe, sans IA : il envoie les demandes aux courtiers de la
liste validée, relève les réponses dans la boîte d'envoi, relance après un mois
sans réponse et écrit un point hebdomadaire.

Commandes :
  envoyer [--n N]   envoie les N prochaines demandes dues (par défaut 2)
  relever           lit les réponses reçues et met à jour l'état de chaque courtier
  relancer          relance les demandes restées sans réponse depuis un mois
  point             envoie le point hebdomadaire à l'utilisateur
  etat              affiche l'état de chaque courtier
  noter ID [--date] enregistre une demande faite hors de l'agent (elle est ensuite suivie et relancée)
Option --essai : rien n'est envoyé ; les mails sont écrits dans donnees/apercus/.

Données personnelles (hors dépôt), dans le dossier donné par EFFACEMENT_DONNEES
(par défaut ../donnees) :
  identite.json     nom, mails, téléphones, adresses, expéditeur, destinataire du point
  acces.json        accès à la boîte d'envoi : {"smtp": ..., "imap": ..., "utilisateur": ..., "mot_de_passe": ...}
  journal.json      état de chaque courtier (écrit par le programme)
  journal.log       trace de chaque action
"""
import argparse, email, email.utils, imaplib, json, os, re, smtplib, sys
from datetime import date, datetime, timedelta
from email.header import decode_header, make_header
from email.message import EmailMessage
from email.utils import make_msgid, formatdate
from pathlib import Path

os.umask(0o077)   # tout ce que l'agent écrit (journal, copies, dossiers) n'est lisible que par l'utilisateur
ICI = Path(__file__).resolve().parent
DONNEES = Path(os.environ.get("EFFACEMENT_DONNEES", ICI.parent / "donnees"))
DELAI_RELANCE = 30        # jours : article 12.3 du RGPD, un mois
DELAI_RECLAMATION = 30    # jours après la relance avant de préparer une réclamation CNIL
RENOUVELLEMENT = 90       # jours : demandes renouvelées tous les trois mois

# États d'un courtier
A_ENVOYER = "à envoyer"
ENVOYE = "envoyé"
RELANCE = "relancé"
CONFIRME = "effacement confirmé"
AUCUNE_DONNEE = "aucune donnée détenue"
VERIFICATION = "vérification à faire"
PIECE = "pièce demandée"
PIECE_ENVOYEE = "pièce d'identité envoyée"
REDIRECTION = "renvoie vers son formulaire"
ACCUSE = "accusé de réception"
REFUS = "refus"
A_LIRE = "réponse à lire"
CNIL = "réclamation CNIL prête"
REUSSITES = {CONFIRME, AUCUNE_DONNEE}
REMONTE = {PIECE, REFUS, A_LIRE, CNIL, VERIFICATION}   # ces cas vont à l'utilisateur

# Mots qui classent une réponse ; l'ordre compte (le premier qui correspond gagne).
REGLES = [
    # Pièce : seulement quand un DOCUMENT est demandé (copie, scan, photo d'une pièce). « Vérifier votre identité »
    # par un lien à cliquer n'en est pas une : c'est une vérification.
    (PIECE, r"pi[eè]ce d.identit|justificatif d.identit|carte d.identit|passeport|passport|proof of identity|identity document|photo id|government.issued id|copy of (your |an )?(id|identification|passport)|copie de (votre |votre )?(pi[eè]ce|carte|passeport)"),
    # Le courtier renvoie vers son formulaire : le mail reste valable (CEPD, lignes directrices 01/2022, points 52-53).
    (REDIRECTION, r"privacy cent(er|re)|privacy portal|dsar portal|web ?form|our (online )?form|notre formulaire|formulaire (en ligne|d[ée]di[ée])|submit (your|a) request (via|through|on|using)|please (use|visit|fill)|veuillez (utiliser|remplir|passer par)"),
    (VERIFICATION, r"verify your|(v[ée]rifier|confirmer|prouver) votre identit|(verify|confirm|prove) your identity|identity verification|v[ée]rifi(er|ez|cation)|confirm your (email|request)|confirmez votre|cliquez sur le lien|click (the|this) link"),
    (AUCUNE_DONNEE, r"aucune donn[ée]e|aucune information|n.avons pas d.informations?|pas d.informations? (associ|vous concern)|no (personal )?(data|information|record)s? (was |were )?(found|held)|not (found|hold|have any)|ne (d[ée]tenons|disposons) (pas|d.aucune)"),
    (CONFIRME, r"(a|ont) (bien )?[ée]t[ée] (supprim|effac)|a honor[ée] votre demande|has honou?red your|bien (supprim|effac)|have been (deleted|removed|erased)|has been (deleted|removed|erased)|suppression (est )?effectu|deletion (is )?complete|successfully (deleted|removed)"),
    (ACCUSE, r"bien re[çc]u|(have|has) received your|accus[ée] de r[ée]ception|we received your|nous traitons votre demande|in progress|en cours de traitement"),
    (REFUS, r"refus|ne pouvons pas|pas en mesure|unable to|cannot (delete|erase|process)|we decline|int[ée]r[êe]t l[ée]gitime"),
]


def log(m):
    DONNEES.mkdir(parents=True, exist_ok=True)
    with open(DONNEES / "journal.log", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%F %T} {m}\n")
    print(m)


def charger(nom, defaut=None):
    p = DONNEES / nom
    if not p.exists():
        if defaut is not None:
            return defaut
        sys.exit(f"manque {p} (données personnelles, hors dépôt)")
    return json.loads(p.read_text(encoding="utf-8"))


def sauver_journal(j):
    p = DONNEES / "journal.json"
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)


def courtiers():
    """La liste commune (dépôt), plus les courtiers que l'utilisateur a validés pour lui (donnees/, hors dépôt)."""
    liste = json.loads((ICI / "courtiers.json").read_text(encoding="utf-8"))
    ajouts = charger("courtiers-ajoutes.json", [])
    par_id = {c["id"]: c for c in liste}
    for c in ajouts:
        par_id[c["id"]] = {**par_id.get(c["id"], {}), **c}
    return list(par_id.values())


def journal():
    j = charger("journal.json", {})
    for c in courtiers():
        j.setdefault(c["id"], {"etat": A_ENVOYER, "envois": [], "reponses": []})
    return j


# ---------- le modèle validé ----------

sys.path.insert(0, str(ICI))   # lancé avec python -I : le dossier du script n'est pas dans le chemin
import textes as T  # noqa: E402


def OBJ(ident):
    return T.OBJET[T.langue(ident)]


def corps_demande(ident, relance_du=None):
    return T.demande(ident, relance_du)


# ---------- envoi ----------

def envoyer_mail(dest, objet, corps, essai, ident, copie=None, pieces=()):
    """copie : nom du fichier où garder le mail envoyé (donnees/envois/), preuve pour une réclamation.
    pieces : fichiers joints (le point du lundi joint les dossiers de réclamation prêts)."""
    msg = EmailMessage()
    msg["From"] = f"{ident['nom']} <{ident['expediteur']}>"
    msg["To"] = dest
    msg["Subject"] = objet
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=ident["expediteur"].split("@")[1])
    msg.set_content(corps)
    for f in pieces:
        f = Path(f)
        msg.add_attachment(f.read_bytes(), maintype="application", subtype="octet-stream", filename=f.name)
    if essai:
        d = DONNEES / "apercus"
        d.mkdir(parents=True, exist_ok=True)
        f = d / f"{datetime.now():%Y%m%d-%H%M%S}-{re.sub(r'[^a-z0-9]', '_', dest.lower())}.eml"
        f.write_bytes(bytes(msg))
        log(f"ESSAI : mail non envoyé à {dest} (aperçu {f.name})")
        return msg["Message-ID"]
    a = charger("acces.json")
    with smtplib.SMTP_SSL(a["smtp"], 465, timeout=60) as s:
        s.login(a["utilisateur"], a["mot_de_passe"])
        s.send_message(msg)
    log(f"mail envoyé à {dest} : « {objet} »")
    if copie:
        d = DONNEES / "envois"
        d.mkdir(parents=True, exist_ok=True)
        (d / copie).write_bytes(bytes(msg))
    return msg["Message-ID"]


def cycle(e):
    """Date de la demande du cycle en cours (la dernière « demande »), et la date de sa relance s'il y en a une."""
    debut = max((x["date"] for x in e["envois"] if x.get("type") == "demande" and not x.get("essai")), default=None)
    relance = max((x["date"] for x in e["envois"] if x.get("type") == "relance" and debut and x["date"] >= debut
                   and not x.get("essai")), default=None)
    return (date.fromisoformat(debut) if debut else None), (date.fromisoformat(relance) if relance else None)


def dus(j, maintenant):
    """Courtiers à qui une demande est due : jamais envoyée, ou demande du cycle en cours vieille de 3 mois ou plus."""
    out = []
    for c in courtiers():
        e = j[c["id"]]
        if c.get("canal") != "mail" or not c.get("adresse"):
            continue
        debut, _ = cycle(e)
        if not debut:
            out.append((date.min, c))
        elif (maintenant - debut).days >= RENOUVELLEMENT and e["etat"] not in (PIECE, REFUS, A_LIRE, CNIL):
            out.append((debut, c))
    out.sort(key=lambda x: x[0])
    return [c for _, c in out]


def cmd_envoyer(n, essai):
    ident, j, auj = charger("identite.json"), journal(), date.today()
    faits = 0
    for c in dus(j, auj):
        if faits >= n:
            break
        e = j[c["id"]]
        if c.get("canal") != "mail" or not c.get("adresse") or not _domaine_dans(c["adresse"].rsplit("@", 1)[-1].lower(), c.get("domaines", [])):
            # Le projet n'écrit que par mail, et seulement à une adresse d'un domaine du courtier (article 12 du RGPD) : un courtier sans adresse publiée attend la sienne.
            continue
        if c["canal"] == "mail":
            mid = envoyer_mail(c["adresse"], OBJ(ident), corps_demande(ident), essai, ident,
                               copie=f"{auj.isoformat()}-{c['id']}-demande.eml")
            e["envois"].append({"date": auj.isoformat(), "type": "demande", "canal": "mail", "message_id": mid, "essai": essai})
            e["etat"] = ENVOYE
        faits += 1
        if not essai:
            sauver_journal(j)   # après chaque envoi : un arrêt en route ne fait jamais renvoyer deux fois
    if not essai:
        sauver_journal(j)
    log(f"envoyer : {faits} demande(s) traitée(s){' (essai)' if essai else ''}")


# ---------- relevé des réponses ----------

def decoder(v):
    try:
        return str(make_header(decode_header(v or "")))
    except Exception:
        return v or ""


def texte(msg):
    morceaux = []
    for part in msg.walk():
        if part.get_content_type() in ("text/plain", "text/html") and not part.get_filename():
            try:
                t = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", "replace")
            except Exception:
                continue
            if part.get_content_type() == "text/html":
                t = re.sub(r"(?s)<[^>]+>", " ", t)
            morceaux.append(t)
    return re.sub(r"\s+", " ", " ".join(morceaux))


def classer(t):
    t = t.lower()
    for etat, motif in REGLES:
        if re.search(motif, t):
            return etat
    return A_LIRE


def cmd_relever(essai):
    a, j = charger("acces.json"), journal()
    debut = min((date.fromisoformat(e["envois"][0]["date"]) for e in j.values() if e["envois"]), default=None)
    if not debut:
        log("relever : aucune demande envoyée, rien à lire")
        return
    vus = {r["id"] for e in j.values() for r in e["reponses"]}
    M = imaplib.IMAP4_SSL(a["imap"])
    M.login(a["utilisateur"], a["mot_de_passe"])
    nouveaux = 0
    for boite in ("INBOX", "Bulk", "Spam", "Junk", '"[Gmail]/Spam"'):
        if M.select(boite, readonly=True)[0] != "OK":
            continue
        for c in courtiers():
            e = j[c["id"]]
            if not e["envois"]:
                continue
            depuis = date.fromisoformat(e["envois"][0]["date"]).strftime("%d-%b-%Y")
            # domaines du courtier ; pour ceux qui répondent par un prestataire partagé (OneTrust…), un mot du nom
            # de l'expéditeur (« expediteurs ») ou de l'objet (« objets ») propre au courtier
            criteres = [f'FROM "@{d}"' for d in c["domaines"]] + [f'FROM "{x}"' for x in c.get("expediteurs", [])] \
                + [f'SUBJECT "{x}"' for x in c.get("objets", [])]
            for critere in criteres:
                _, ids = M.search(None, f'(SINCE {depuis} {critere})')
                for i in ids[0].split():
                    _, d = M.fetch(i, "(RFC822)")
                    msg = email.message_from_bytes(d[0][1])
                    mid = msg.get("Message-ID") or f"{boite}-{i.decode()}"
                    if mid in vus:
                        continue
                    t = texte(msg)
                    etat = classer(t)
                    # le mail d'origine est gardé tel quel : pièce d'une éventuelle plainte
                    fichier = None
                    if not essai:
                        dr = DONNEES / "reponses"
                        dr.mkdir(parents=True, exist_ok=True)
                        fichier = f"{date.today().isoformat()}-{c['id']}-{len(e['reponses']) + 1:02d}.eml"
                        (dr / fichier).write_bytes(d[0][1])
                    e["reponses"].append({"id": mid, "date": decoder(msg.get("Date")), "de": decoder(msg.get("From")),
                                          "objet": decoder(msg.get("Subject")), "classe": etat, "extrait": t[:400],
                                          "fichier": fichier})
                    vus.add(mid)
                    # Une réussite ne se perd pas sur un accusé de réception suivant.
                    if etat == ACCUSE:
                        pass  # le courtier a reçu la demande : l'état ne change pas, le délai court toujours
                    elif e["etat"] not in REUSSITES or etat in REUSSITES:
                        e["etat"] = etat
                    if etat == REDIRECTION:
                        ok, note = rappeler_canal(c, e, msg, charger("identite.json"), essai)
                        log(f"{c['nom']} : {note}")
                        e["etat"] = ENVOYE
                    if etat == VERIFICATION:
                        ok, note = suivre_lien(c, msg, essai)
                        log(f"{c['nom']} : lien de vérification {'suivi' if ok else 'non suivi'} ({note})")
                        if ok:
                            e["etat"] = ENVOYE
                    if etat == PIECE:
                        ok, note = envoyer_piece(c, e, msg, charger("identite.json"), essai)
                        log(f"{c['nom']} : pièce d'identité {'envoyée' if ok else 'non envoyée'} ({note})")
                        if ok:
                            e["etat"] = PIECE_ENVOYEE
                    nouveaux += 1
                    if not essai:
                        sauver_journal(j)   # après chaque réponse traitée : un arrêt ne fait jamais renvoyer un mail
                    log(f"réponse de {c['nom']} : {etat} (« {decoder(msg.get('Subject'))[:80]} »)")
    chercher_validation(M, charger("identite.json"), essai)
    M.logout()
    if not essai:
        sauver_journal(j)
    log(f"relever : {nouveaux} nouvelle(s) réponse(s)")


# ---------- courtier qui renvoie vers son formulaire ----------

def corps_rappel_canal(ident, depuis):
    return T.rappel_canal(ident, depuis)


def rappeler_canal(c, e, msg, ident, essai):
    if c.get("canal") != "mail" or not c.get("adresse"):
        return False, "pas d'adresse validée"
    if any(x.get("type") == "rappel-canal" for x in e["envois"]):
        return False, "déjà rappelé une fois : la relance à un mois suivra"
    premiere = next((x["date"] for x in e["envois"] if x.get("type") == "demande"), date.today().isoformat())
    objet = decoder(msg.get("Subject")) or OBJ(ident)
    objet = objet if objet.lower().startswith("re:") else "Re: " + objet
    mid = envoyer_mail(c["adresse"], objet, corps_rappel_canal(ident, date.fromisoformat(premiere).strftime("%d/%m/%Y")),
                       essai, ident, copie=f"{date.today().isoformat()}-{c['id']}-rappel-canal.eml")
    e["envois"].append({"date": date.today().isoformat(), "type": "rappel-canal", "canal": "mail", "message_id": mid, "essai": essai})
    return True, f"rappel envoyé à {c['adresse']} : le mail suffit"


# ---------- pièce d'identité (décision de l'utilisateur : envoi automatique, avec garde-fous) ----------

def _domaine_dans(dom, domaines):
    return any(dom == d or dom.endswith("." + d) for d in domaines)


def authentifie(msg, c, domaines=None):
    """Vrai seulement si le PREMIER en-tête Authentication-Results (celui qu'ajoute ton propre fournisseur ; ceux
    plus bas peuvent avoir été écrits par l'expéditeur) dit dkim=pass pour un domaine exact du courtier, et si
    l'expéditeur affiché est de ce même domaine."""
    domaines = domaines or c["domaines"]
    de = (email.utils.parseaddr(decoder(msg.get("From")))[1] or "").lower()
    dom_de = de.rsplit("@", 1)[-1]
    if not _domaine_dans(dom_de, domaines):
        return False
    tous = msg.get_all("Authentication-Results") or []
    if not tous:
        return False
    res = str(tous[0]).lower()
    for m in re.finditer(r"dkim=pass\b([^;]*)", res):
        for d_sig in re.findall(r"header\.(?:d|i)=@?([a-z0-9.-]+?)(?=[\s;)]|$)", m.group(1)):
            if _domaine_dans(d_sig, domaines) and (dom_de == d_sig or dom_de.endswith("." + d_sig)):
                return True
    return False


def suivre_lien(c, msg, essai):
    """Confirme une demande par le lien reçu (« confirmez votre adresse », « vérifiez votre identité en cliquant ») :
    seulement si le mail est authentifié pour un domaine du courtier, et seulement le lien de confirmation."""
    if not authentifie(msg, c):
        return False, "mail non authentifié pour le domaine du courtier"
    html = ""
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            html = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", "replace")
            break
    liens = re.findall(r'<a[^>]+href="(https://[^"]+)"[^>]*>(.*?)</a>', html, re.S | re.I)
    cible = next((u for u, t in liens if re.search(r"confirm|verif|v[ée]rif|valid", u + " " + re.sub(r"<[^>]+>", " ", t), re.I)
                  and not re.search(r"unsubscribe|d[ée]sinscri|privacy-policy|politique", u, re.I)), None)
    if not cible:
        return False, "aucun lien de confirmation trouvé"
    from urllib.parse import urlparse
    hote = (urlparse(cible).hostname or "").lower()
    if not _domaine_dans(hote, c["domaines"] + c.get("hotes_liens", [])):
        return False, f"lien hors des domaines du courtier ({hote}) : non ouvert"
    if essai:
        return True, f"ESSAI : lien non ouvert ({cible[:60]}…)"
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            nav = p.chromium.launch(headless=True)
            page = nav.new_page(locale="fr-FR")
            page.goto(cible, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(3000)
            corps = page.inner_text("body")[:2000]
            nav.close()
    except Exception as ex:
        return False, f"ouverture impossible ({type(ex).__name__})"
    if re.search(r"confirm|verified|v[ée]rifi|thank|merci|success|valid", corps, re.I) and not re.search(r"expired|expir[ée]|invalid", corps, re.I):
        return True, "confirmation vue sur la page"
    return False, "page ouverte sans confirmation reconnue : " + re.sub(r"\s+", " ", corps)[:120]


def filigraner(source, texte):
    """Copie de la pièce, barrée en diagonale d'un filigrane répété qui limite son usage (fait sur la machine,
    jamais envoyé à un service en ligne)."""
    from PIL import Image, ImageDraw, ImageFont
    im = Image.open(source).convert("RGB")
    w, h = im.size
    taille = max(18, w // 28)
    try:
        police = ImageFont.truetype("DejaVuSans-Bold.ttf", taille)
    except OSError:
        police = ImageFont.load_default()
    calque = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    dessin = ImageDraw.Draw(calque)
    pas = int(taille * 2.6)
    for y in range(0, h * 2, pas):
        dessin.text((((y // pas) % 2) * pas, y), (texte + "   ") * 6, font=police, fill=(200, 0, 0, 110))
    calque = calque.rotate(30, expand=False).crop((w // 2, h // 2, w // 2 + w, h // 2 + h))
    im = Image.alpha_composite(im.convert("RGBA"), calque).convert("RGB")
    sortie = DONNEES / "pieces" / f"piece-{date.today().isoformat()}.jpg"
    sortie.parent.mkdir(parents=True, exist_ok=True)
    im.save(sortie, quality=85)
    return sortie


def envoyer_piece(c, e, msg, ident, essai):
    """Répond à une demande de pièce d'identité : seulement si le mail est authentifié pour un domaine du courtier,
    seulement à l'adresse validée de la liste (jamais à l'adresse de la demande), avec une copie filigranée."""
    source = next(iter(sorted((DONNEES).glob("piece-identite.*"))), None)
    if not source:
        return False, "aucune pièce d'identité fournie"
    if c.get("canal") != "mail" or not c.get("adresse"):
        return False, "pas d'adresse validée pour ce courtier"
    if not authentifie(msg, c):
        return False, "mail non authentifié pour le domaine du courtier : possible faux"
    if any(x.get("type") == "piece" for x in e["envois"]):
        return False, "pièce déjà envoyée une fois à ce courtier"
    texte = f"Demande RGPD a {c['nom']} - {date.today():%d/%m/%Y} - usage unique"
    try:
        piece = filigraner(source, texte)
    except Exception as ex:  # Pillow absent, image illisible : la demande remonte, rien ne part
        return False, f"filigrane impossible ({type(ex).__name__}) : installer Pillow"
    corps = T.piece(ident)
    objet = decoder(msg.get("Subject")) or OBJ(ident)
    objet = objet if objet.lower().startswith("re:") else "Re: " + objet
    mid = envoyer_mail(c["adresse"], objet, corps, essai, ident,
                       copie=f"{date.today().isoformat()}-{c['id']}-piece.eml", pieces=[piece])
    e["envois"].append({"date": date.today().isoformat(), "type": "piece", "canal": "mail", "message_id": mid, "essai": essai})
    return True, f"copie filigranée envoyée à {c['adresse']}"


# ---------- validation des nouveaux courtiers (réponse « OUI » au point) ----------

PROPOSES = DONNEES / "courtiers-proposes.json"   # propositions de l'agent de recherche, propres à l'utilisateur


def propositions():
    if not PROPOSES.exists():
        return [], []
    d = json.loads(PROPOSES.read_text(encoding="utf-8"))
    return d.get("a_valider", []), d.get("corrections", [])


def chercher_validation(M, ident, essai):
    """Si l'utilisateur a répondu « OUI » au dernier point (mail authentifié de sa propre adresse),
    les courtiers proposés entrent dans sa liste, et les adresses corrigées sont mises à jour."""
    v = charger("validation.json", {})
    if not v.get("ids") and not v.get("corrections"):
        return
    moi = ident["destinataire_point"].lower()
    dom = moi.rsplit("@", 1)[-1]
    M.select("INBOX", readonly=True)
    depuis = date.fromisoformat(v["date"]).strftime("%d-%b-%Y")
    _, ids = M.search(None, f'(SINCE {depuis} FROM "{moi}")')
    for i in ids[0].split():
        _, d = M.fetch(i, "(RFC822)")
        msg = email.message_from_bytes(d[0][1])
        if v["objet"] not in decoder(msg.get("Subject")):
            continue
        if not authentifie(msg, {"domaines": [dom]}):
            log("réponse au point non authentifiée : ignorée")
            continue
        if not re.match(r"\s*(oui|yes)\b", texte(msg), re.I):
            continue
        a_valider, corrections = propositions()
        connus = {c["id"] for c in courtiers()}
        ajout = [{k: x[k] for k in ("id", "nom", "canal", "adresse", "domaines", "pays", "source", "vu_le") if k in x}
                 for x in a_valider if x["id"] in v["ids"] and x["id"] not in connus]
        corr = {x["id"]: x for x in corrections if x["id"] in v.get("corrections", [])}
        ajout += [{"id": i, "adresse": x["nouvelle"], "source": x["source"], "vu_le": x["vu_le"]} for i, x in corr.items()]
        if essai:
            log(f"ESSAI : {len(ajout) - len(corr)} courtier(s) et {len(corr)} correction(s) seraient validés")
            return
        anciens = charger("courtiers-ajoutes.json", [])
        ids = {x["id"] for x in ajout}
        (DONNEES / "courtiers-ajoutes.json").write_text(json.dumps([x for x in anciens if x["id"] not in ids] + ajout,
                                                                  ensure_ascii=False, indent=1), encoding="utf-8")
        d2 = json.loads(PROPOSES.read_text(encoding="utf-8"))
        d2["a_valider"] = [x for x in d2.get("a_valider", []) if x["id"] not in v["ids"]]
        d2["corrections"] = [x for x in d2.get("corrections", []) if x["id"] not in corr]
        PROPOSES.write_text(json.dumps(d2, ensure_ascii=False, indent=1), encoding="utf-8")
        (DONNEES / "validation.json").write_text("{}")
        log(f"validation reçue : {len(ajout) - len(corr)} courtier(s) ajouté(s), {len(corr)} adresse(s) corrigée(s)")
        return


# ---------- relances ----------

def cmd_relancer(essai):
    """Relance un mois après la demande (article 12.3), puis prépare la plainte un mois après la relance.
    Les délais se comptent depuis la demande du cycle, pas depuis le dernier mail."""
    ident, j, auj = charger("identite.json"), journal(), date.today()
    for c in courtiers():
        e = j[c["id"]]
        if e["etat"] not in (ENVOYE, RELANCE, PIECE_ENVOYEE) or c.get("canal") != "mail" or not c.get("adresse"):
            continue
        debut, relance = cycle(e)
        if not debut:
            continue
        if not relance and (auj - debut).days >= DELAI_RELANCE:
            mid = envoyer_mail(c["adresse"], T.PREFIXE_RELANCE[T.langue(ident)] + OBJ(ident), corps_demande(ident, relance_du=debut.strftime("%d/%m/%Y")),
                               essai, ident, copie=f"{auj.isoformat()}-{c['id']}-relance.eml")
            e["envois"].append({"date": auj.isoformat(), "type": "relance", "canal": "mail", "message_id": mid, "essai": essai})
            e["etat"] = RELANCE
            log(f"{c['nom']} : relancé ({(auj - debut).days} jours après la demande)")
            if not essai:
                sauver_journal(j)
        elif relance and (auj - relance).days >= DELAI_RECLAMATION:
            if essai:
                log(f"ESSAI : {c['nom']} : réclamation CNIL serait préparée")
                continue
            e["etat"] = CNIL
            dossier = preparer_reclamation(c, e, ident)
            log(f"{c['nom']} : sans réponse après relance, réclamation CNIL prête ({dossier.name})")
            sauver_journal(j)


# ---------- réclamation CNIL ----------

def preparer_reclamation(c, e, ident):
    """Prépare, sans rien déposer, le dossier de plainte en ligne (cnil.fr/fr/plaintes) : le texte à coller
    et les pièces numérotées (copie de la demande, de la relance, des réponses éventuelles)."""
    import zipfile
    d = DONNEES / "cnil"
    d.mkdir(parents=True, exist_ok=True)
    envois = [x for x in e["envois"] if not x.get("essai")]
    dates = "\n".join(f"- {date.fromisoformat(x['date']).strftime('%d/%m/%Y')} : "
                       f"{'demande' if x['type'] == 'demande' else 'relance'} ({x['canal']})" for x in envois)
    texte = T.plainte(ident, f"{c['nom']}" + (f", {c['adresse']}" if c.get("adresse") else ""), dates)
    z = d / f"{date.today().isoformat()}-{c['id']}-reclamation.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("00-texte-de-la-plainte.txt", texte)
        n = 1
        for x in envois:
            f = DONNEES / "envois" / f"{x['date']}-{c['id']}-{x['type']}.eml"
            if f.exists():
                zf.write(f, f"{n:02d}-{x['type']}-{x['date']}.eml")
            else:  # envoi antérieur à la conservation des copies : texte reconstitué, signalé comme tel
                zf.writestr(f"{n:02d}-{x['type']}-{x['date']}-reconstitue.txt",
                            f"Copie reconstituée du modèle envoyé le {x['date']} ({x['canal']}).\n\n" + corps_demande(ident))
            n += 1
        for r in e["reponses"]:
            f = DONNEES / "reponses" / (r.get("fichier") or "-")
            if r.get("fichier") and f.exists():
                zf.write(f, f"{n:02d}-reponse.eml")
            else:  # réponse notée sans le mail d'origine : extrait seulement, signalé comme tel
                zf.writestr(f"{n:02d}-reponse-extrait.txt", f"Extrait (le mail d'origine n'a pas été conservé)\nDe : {r['de']}\nDate : {r['date']}\nObjet : {r['objet']}\n\n{r['extrait']}\n")
            n += 1
    return z


# ---------- point hebdomadaire ----------

def resume(j):
    lignes, total, reussis = [], 0, 0
    for c in courtiers():
        e = j[c["id"]]
        total += 1
        reussis += e["etat"] in REUSSITES
        dernier = e["envois"][-1]["date"] if e["envois"] else "jamais"
        lignes.append((e["etat"], c["nom"], dernier))
    return lignes, total, reussis


def cmd_point(essai):
    ident, j = charger("identite.json"), journal()
    lignes, total, reussis = resume(j)
    a_toi = [l for l in lignes if l[0] in REMONTE]
    P = T.POINT[T.langue(ident)]
    corps = [P["score"].format(ok=reussis, total=total), ""]
    if a_toi:
        corps.append(P["a_toi"])
        corps += [f"• {nom} : {T.etat(ident, etat)}" for etat, nom, _ in a_toi]
        corps.append("")
    corps.append(P["etat"])
    corps += [f"• {nom} : {T.etat(ident, etat)} ({P['dernier']} : {d if d != 'jamais' else P['jamais']})" for etat, nom, d in sorted(lignes)]
    texte_point = "\n".join(corps) + "\n"
    objet = P["objet"].format(date=f"{date.today():%d/%m}", ok=reussis, total=total)
    a_valider, corrections = propositions()
    if a_valider or corrections:
        texte_point += "\n" + P["nouveaux"].format(n=len(a_valider)) + "\n"
        texte_point += "".join(f"• {x['nom']} — {x['adresse']} ({P['source']} : {x['source']})\n" for x in a_valider)
        if corrections:
            texte_point += P["corrections"] + "\n" + "".join(f"• {x['id']} : {x['ancienne']} → {x['nouvelle']} ({P['source']} : {x['source']})\n" for x in corrections)
        texte_point += P["valider"] + "\n"
        if not essai:
            (DONNEES / "validation.json").write_text(json.dumps({"date": date.today().isoformat(), "objet": objet,
                "ids": [x["id"] for x in a_valider], "corrections": [x["id"] for x in corrections]}, ensure_ascii=False))
    prets = sorted((DONNEES / "cnil").glob("*-reclamation.zip")) if (DONNEES / "cnil").exists() else []
    a_joindre = [z for z in prets if not (z.with_suffix(".envoye")).exists()]
    if a_joindre:
        texte_point += "\n" + P["plaintes"].format(url=T.autorite(ident.get("pays", "FR")).get("plainte_url", "")) + "\n"
    envoyer_mail(ident["destinataire_point"], objet, texte_point, essai, ident, pieces=a_joindre)
    if not essai:
        for z in a_joindre:
            z.with_suffix(".envoye").touch()


def cmd_noter(cid, jour, essai):
    """Enregistre une demande faite hors de l'agent : elle est ensuite lue et relancée comme les autres."""
    j = journal()
    if cid not in j:
        sys.exit(f"courtier inconnu : {cid}")
    e = j[cid]
    e["envois"].append({"date": jour, "type": "demande", "canal": "à la main", "ok": True, "essai": essai})
    e["etat"] = ENVOYE
    if not essai:
        sauver_journal(j)
    log(f"{cid} : demande faite à la main le {jour}, {'non enregistrée (essai)' if essai else 'enregistrée'}")


def cmd_etat():
    lignes, total, reussis = resume(journal())
    for etat, nom, d in sorted(lignes):
        print(f"{etat:32} {nom:55} {d}")
    print(f"\n{reussis}/{total} réussites")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("commande", choices=["envoyer", "relever", "relancer", "point", "etat", "noter"])
    p.add_argument("courtier", nargs="?", help="pour noter : identifiant du courtier (voir courtiers.json)")
    p.add_argument("--date", default=date.today().isoformat(), help="pour noter : date de la demande (AAAA-MM-JJ)")
    p.add_argument("--n", type=int, default=2)
    p.add_argument("--essai", action="store_true")
    a = p.parse_args()
    sys.path.insert(0, str(ICI))
    {"envoyer": lambda: cmd_envoyer(a.n, a.essai), "relever": lambda: cmd_relever(a.essai),
     "relancer": lambda: cmd_relancer(a.essai), "point": lambda: cmd_point(a.essai), "etat": cmd_etat,
     "noter": lambda: cmd_noter(a.courtier, a.date, a.essai)}[a.commande]()


if __name__ == "__main__":
    main()
