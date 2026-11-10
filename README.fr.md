# Agent - EU Data Eraser (effaceur de données)

*[English](README.md) · Français*

Un agent permanent pour les personnes qui vivent dans l'Union européenne, la France d'abord pour l'instant. Il tourne sur ta machine et demande, à ta place et en ton nom, aux courtiers en données d'effacer tes données personnelles (droit à l'effacement, article 17 du RGPD). Il fait le travail d'un service comme Incogni, en clair : chaque demande, chaque réponse et chaque relance restent chez toi.

![Schéma : l'agent d'effacement écrit depuis ta boîte au délégué de chaque courtier ; l'agent de recherche propose de nouveaux courtiers à la liste commune](docs/images/schema.svg)

## Ce qu'il fait
- **Il écrit au délégué à la protection des données de chaque courtier**, depuis ta propre boîte mail, avec un modèle repris de la CNIL : effacement (article 17), opposition à la prospection (article 21), notification aux destinataires (article 19). Deux demandes le mardi, deux le jeudi.
- **Il lit les réponses chaque matin** et les classe : effacé, aucune donnée, refus, accusé de réception, pièce demandée. Il suit seul un lien de confirmation authentique, et répond une fois à un courtier qui renvoie vers son formulaire : le mail suffit (voir plus bas).
- **Il relance un mois après la demande** (délai légal, article 12.3), puis, un mois après la relance, **prépare la plainte à la CNIL** : le texte et les pièces numérotées, que tu déposes. Trois mois après la demande, il la renouvelle.
- **Il t'envoie un point chaque lundi** : où en est l'objectif, ce qui t'attend, l'état de chaque courtier, et les nouveaux courtiers à valider.
- **Un agent de recherche** (Claude Code) cherche chaque lundi de nouveaux courtiers et l'adresse que chacun publie. Il ne fait que proposer : une réponse « OUI » au point les ajoute à ta liste.
- **En option, il trie les spams qui passent le filtre** de ta messagerie : chaque matin, un petit modèle d'IA (Claude Haiku) lit les mails arrivés et range les spams dans un dossier à part, listés dans le point du lundi et effacés 30 jours plus tard. Il ne touche jamais aux courriers des courtiers, aux tiens, ni à ceux de quelqu'un à qui tu as écrit. Toute boîte IMAP avec mot de passe d'application (Yahoo, Gmail, iCloud, Fastmail…) ; pas encore Outlook.com, qui exige une connexion OAuth. `installer.py spams oui` pour l'activer, `./lancer.sh tri trier --essai` pour voir ses verdicts sans rien déplacer ; `TRI_CMD` permet d'utiliser un autre modèle.

![Le cycle d'une demande : jour 0 la demande, chaque matin le relevé, à un mois la relance, à deux mois la plainte préparée, à trois mois une nouvelle demande](docs/images/cycle.svg)

## Ce qui reste à toi
Installer une fois, valider le modèle et la liste, dire « OUI » aux nouvelles adresses, déposer une plainte quand l'agent l'a préparée. Aucun mandat à signer : les demandes partent de ta boîte, tu exerces toi-même ton droit. La machine doit rester allumée.

## Le mail suffit
Le RGPD n'impose aucune forme à une demande. Un courtier peut proposer un formulaire, mais une demande envoyée à l'adresse qu'il publie pour les droits est en général effective et doit être traitée (Comité européen de la protection des données, [lignes directrices 01/2022](https://www.edpb.europa.eu/system/files/2023-04/edpb_guidelines_202201_data_subject_rights_access_v2_en.pdf), points 52-53 : écrites pour le droit d'accès, elles appliquent l'article 12 du RGPD, commun à tous les droits). Le projet n'écrit donc que par mail et ne passe jamais par un formulaire ni un captcha.

## Portée
Pour les personnes qui vivent dans l'UE, l'EEE ou au Royaume-Uni. Les demandes partent en français ou en anglais (`langue`), et l'agent cite l'autorité de ton pays et prépare la plainte pour elle : [`docs/autorites.md`](docs/autorites.md) liste les 31 autorités et leur page de plainte, lues sur leurs sites officiels (celui de la Lituanie n'a pas pu être lu). Il a d'abord servi pour de vrai en France ; la liste des courtiers est surtout française et internationale pour l'instant.

## Installation
Le plus simple : cloner le dépôt, copier `skill/effacement-donnees/` dans `~/.claude/skills/`, puis dire à Claude Code « installe l'agent d'effacement ». Il conduit l'installation une question à la fois. À la main :

```sh
git clone https://github.com/anthohunt/agent-eu-data-eraser ~/agent-eu-data-eraser && cd ~/agent-eu-data-eraser
python3 -m venv .venv && .venv/bin/pip install pillow playwright && .venv/bin/playwright install chromium
echo '{"nom": "…", "mails": ["…"], "telephones": ["…"], "adresses": ["…"], "pays": "FR", "langue": "fr", "expediteur": "…", "destinataire_point": "…"}' | python3 installer.py identite
echo '<mot de passe d application>' | python3 installer.py boite yahoo <adresse>   # ou gmail, ou "imap.x:smtp.x"
python3 installer.py piece recto.jpg     # facultatif
python3 installer.py calendrier          # pose les tâches planifiées (cron)
python3 installer.py essai               # un tour à blanc : rien n'est envoyé
python3 installer.py etat
```

Prérequis : Linux ou macOS (le calendrier utilise cron), Python 3.9 ou plus, une machine allumée en permanence. Pillow sert au filigrane de la pièce d'identité, Playwright à suivre les liens de confirmation : sans eux, ces deux cas te remontent au lieu d'être traités seuls. Claude Code sert à l'agent de recherche.

## Avec d'autres outils d'IA
Le cœur est un programme Python ordinaire, sans IA. Le skill d'installation est un texte que n'importe quel agent de code peut suivre (voir [`AGENTS.md`](AGENTS.md)). L'agent de recherche utilise Claude Code par défaut ; `RECHERCHE_CMD` permet d'y brancher toute commande qui lit la consigne sur son entrée et modifie `docs/courtiers-proposes.json` dans son dossier (Codex, Gemini CLI…), avec les mêmes limites : recherche web, lecture de ce dossier, pas de shell. Seul Claude Code a été testé.

## Données et sécurité
Tout ce qui est personnel reste dans `donnees/`, sur ta machine, hors du dépôt. Les risques pris en compte (faux courtier, faux mail qui réclame la pièce d'identité, lien piégé) et leurs parades sont dans [`SECURITY.fr.md`](SECURITY.fr.md).

## La liste des courtiers
[`docs/courtiers.md`](docs/courtiers.md) : chaque courtier, l'adresse qu'il publie et la page source. Elle est ouverte aux contributions, acceptées par un mainteneur humain : voir [`CONTRIBUTING.fr.md`](CONTRIBUTING.fr.md).

## Pour aller plus loin
- [`docs/recherche.md`](docs/recherche.md) : le cadre légal et les sources.
- [`docs/modele-demande.md`](docs/modele-demande.md) : tous les mails que l'agent peut envoyer.
- `effacement/agent.py` : le programme (`python3 agent.py --help`).

## Licence
MIT, voir [`LICENSE`](LICENSE).
