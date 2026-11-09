#!/usr/bin/env python3
"""Installation de l'agent d'effacement, pas à pas (appelé par le skill, ou à la main).

  installer.py identite              lit sur l'entrée standard le JSON des éléments à effacer et l'écrit dans donnees/
  installer.py boite FOURNISSEUR ADRESSE
                                     lit le mot de passe d'application sur l'entrée standard, écrit donnees/acces.json,
                                     teste la connexion (lecture IMAP et envoi SMTP) sans rien envoyer
  installer.py piece FICHIER         copie la pièce d'identité (image) dans donnees/, pour les demandes authentifiées
  installer.py calendrier            pose le calendrier (cron) : envois, relevés, relances, point, recherche
  installer.py essai                 fait un tour complet à blanc : 2 demandes et le point, écrits en aperçu
  installer.py etat                  ce qui est installé et ce qui manque

Aucune donnée personnelle n'entre dans le dépôt : tout va dans donnees/, ignoré par git, lisible par le seul utilisateur.
"""
import imaplib, json, os, shutil, smtplib, subprocess, sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
DONNEES = Path(os.environ.get("EFFACEMENT_DONNEES", ICI / "donnees"))
FOURNISSEURS = {  # serveurs en SSL (IMAP 993, SMTP 465) ; mot de passe d'application obligatoire chez chacun
    "yahoo": ("imap.mail.yahoo.com", "smtp.mail.yahoo.com"),
    "gmail": ("imap.gmail.com", "smtp.gmail.com"),
}
MARQUE = "# effacement-donnees (installé par installer.py)"


def ecrire(nom, contenu):
    DONNEES.mkdir(parents=True, exist_ok=True)
    os.chmod(DONNEES, 0o700)
    p = DONNEES / nom
    old = os.umask(0o077)
    try:
        p.write_text(contenu, encoding="utf-8")
    finally:
        os.umask(old)
    os.chmod(p, 0o600)
    return p


def identite():
    d = json.loads(sys.stdin.read())
    for cle in ("nom", "mails", "expediteur", "destinataire_point"):
        if not d.get(cle):
            sys.exit(f"champ manquant : {cle}")
    d.setdefault("telephones", []); d.setdefault("adresses", [])
    print(ecrire("identite.json", json.dumps(d, ensure_ascii=False, indent=1)))


def boite(fournisseur, adresse):
    mdp = sys.stdin.readline().strip().replace(" ", "")
    if fournisseur in FOURNISSEURS:
        imap, smtp = FOURNISSEURS[fournisseur]
    elif ":" in fournisseur:  # autre fournisseur : "imap.exemple.fr:smtp.exemple.fr"
        imap, smtp = fournisseur.split(":", 1)
    else:
        sys.exit("fournisseur inconnu : yahoo, gmail, ou « serveur-imap:serveur-smtp »")
    try:
        M = imaplib.IMAP4_SSL(imap); M.login(adresse, mdp); M.logout()
        s = smtplib.SMTP_SSL(smtp, 465, timeout=30); s.login(adresse, mdp); s.quit()
    except (imaplib.IMAP4.error, smtplib.SMTPException, OSError) as e:
        sys.exit(f"connexion refusée ({type(e).__name__}) : vérifier l'adresse et le mot de passe d'application ; rien n'est enregistré")
    ecrire("acces.json", json.dumps({"smtp": smtp, "imap": imap, "utilisateur": adresse, "mot_de_passe": mdp}))
    print("connexion vérifiée (lecture et envoi), accès enregistré dans donnees/acces.json")


def piece(fichier):
    f = Path(fichier)
    if f.suffix.lower() not in (".jpg", ".jpeg", ".png"):
        sys.exit("une image JPG ou PNG du recto")
    DONNEES.mkdir(parents=True, exist_ok=True)
    for vieux in DONNEES.glob("piece-identite.*"):
        vieux.unlink()
    dest = DONNEES / f"piece-identite{f.suffix.lower()}"
    shutil.copyfile(f, dest); os.chmod(dest, 0o600)
    print(dest)


def calendrier():
    l = str(ICI / "lancer.sh"); r = str(ICI / "recherche" / "lancer.sh")
    bloc = [MARQUE,
            f"0 9 * * * {l} relever; {l} relancer",
            f"0 10 * * 2,4 {l} envoyer --n 2",
            f"0 6 * * 1 {r}",
            f"45 7 * * 1 {l} relever",
            f"0 8 * * 1 {l} point",
            MARQUE + " fin"]
    actuel = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout.splitlines()
    garde, dedans = [], False
    for x in actuel:  # remplace l'ancien bloc, et toute ligne qui appelle déjà ce dépôt
        if x == MARQUE: dedans = True; continue
        if x == MARQUE + " fin": dedans = False; continue
        if dedans or str(ICI) in x or "effacement-donnees/" in x or (x.startswith("#") and "effacement" in x.lower()):
            continue
        garde.append(x)
    subprocess.run(["crontab", "-"], input="\n".join(garde + bloc) + "\n", text=True, check=True)
    print("\n".join(bloc[1:-1]))


def essai():
    py = ICI / ".venv" / "bin" / "python"
    py = str(py) if py.exists() else sys.executable
    for cmd in (["envoyer", "--essai", "--n", "2"], ["point", "--essai"]):
        subprocess.run([py, "-I", "agent.py", *cmd], cwd=ICI / "effacement", check=True)
    print(f"aperçus : {DONNEES / 'apercus'}")


def etat():
    for nom, ok in (("éléments à effacer", (DONNEES / "identite.json").exists()),
                    ("boîte d'envoi", (DONNEES / "acces.json").exists()),
                    ("pièce d'identité (facultative)", any(DONNEES.glob("piece-identite.*"))),
                    ("calendrier", MARQUE in subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout)):
        print(f"{'OK ' if ok else '-- '} {nom}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    {"identite": lambda: identite(), "boite": lambda: boite(a[1], a[2]), "piece": lambda: piece(a[1]),
     "calendrier": calendrier, "essai": essai, "etat": etat}[a[0]]()
