---
name: effacement-donnees
description: Installe et règle l'agent d'effacement de données personnelles (droit à l'effacement, article 17 du RGPD) — un programme qui écrit aux courtiers en données depuis la boîte mail de l'utilisateur, suit les réponses, relance après un mois, prépare la plainte CNIL et fait un point chaque lundi, plus un agent de recherche qui propose de nouveaux courtiers chaque semaine. Déclencheurs : « /effacement-donnees », « installe l'agent d'effacement », « fais effacer mes données chez les courtiers », « comme Incogni mais chez moi », « change mes réglages d'effacement ».
---

# Agent d'effacement de données — installation

Tu installes, avec l'utilisateur, le dépôt `effacement-donnees` sur SA machine. Tu parles français, simplement, **une question à la fois**, chaque question à choix avec des options A/B/C et une option ouverte. Tout ce qui est personnel va dans `donnees/` (ignoré par git, lisible par le seul utilisateur) par `installer.py` ; rien de personnel n'entre jamais dans le dépôt, ni dans une demande de fusion.

## 0. Dire d'abord ce que c'est, et ce qui restera à l'utilisateur
En 3 lignes : l'agent écrit en son nom, depuis sa propre boîte, au délégué à la protection des données de chaque courtier de la liste ; il relance après un mois (article 12.3 du RGPD) ; il lui envoie un point chaque lundi. Restent à l'utilisateur : valider une fois le modèle et la liste, valider chaque nouvelle adresse d'un « OUI » au point, et déposer lui-même une plainte à la CNIL quand l'agent l'a préparée. La machine doit rester allumée (le calendrier tourne dessus). Aucun mandat à signer : il exerce lui-même son droit.

## 1. Le dépôt
S'il n'est pas déjà là : `git clone <adresse du dépôt public> ~/effacement-donnees`. Vérifier `python3 --version` (3.9 ou plus). L'agent de recherche a besoin de Claude Code (`claude`) sur la machine.

## 2. Les éléments à effacer (un par un)
Nom tel qu'il apparaît dans les fichiers ; toutes ses adresses mail ; ses numéros de téléphone ; ses adresses postales, anciennes comprises (les fichiers de prospection les gardent longtemps). Expliquer en une phrase : ce sont les clés avec lesquelles chaque courtier cherche sa fiche ; plus il y en a, plus on la trouve. Puis :
`echo '{"nom":…,"mails":[…],"telephones":[…],"adresses":[…],"expediteur":"<boîte d'envoi>","destinataire_point":"<où recevoir le point>"}' | python3 installer.py identite`

## 3. La boîte d'envoi
Celle d'où partent les demandes (une de ses adresses : la demande prouve alors qu'elle lui appartient). Fournisseur : A Yahoo, B Gmail, C autre (demander ses serveurs IMAP et SMTP en SSL). Lui faire créer un **mot de passe d'application réservé à cet agent** (Yahoo : Sécurité du compte › Connexions externes ; Gmail : Compte Google › Sécurité › Mots de passe des applications, validation en deux étapes requise) et le lui faire dicter ; ne jamais le recopier ailleurs. Lui dire : pour couper l'agent, il suffit de supprimer ce mot de passe chez le fournisseur.
`echo '<mot de passe>' | python3 installer.py boite yahoo <adresse>` — le script vérifie la lecture et l'envoi, sans rien envoyer.

## 4. Le modèle et la liste : une seule validation
Montrer le modèle (`docs/modele-demande.md`) tel qu'il partira, et la liste (`effacement/courtiers.json` : nom et adresse de chaque courtier). Il peut retirer des courtiers. Son « oui » vaut pour tous les envois et relances futurs vers ces adresses ; toute nouvelle adresse lui sera redemandée.

## 5. La pièce d'identité (facultative)
Expliquer le risque d'abord, avec un exemple : un faux mail « du courtier » qui réclame la carte pour usurper son identité. Garde-fous de l'agent : il ne répond qu'à une demande signée (DKIM) par le domaine du courtier, seulement à l'adresse validée de la liste, une fois par courtier, avec une copie barrée d'un filigrane « Demande RGPD à <courtier>, <date>, usage unique ». Un courtier ne peut l'exiger qu'en cas de doute raisonnable (article 12.6). Choix : A fournir une photo du recto (`python3 installer.py piece <fichier>`) ; B non, chaque demande de pièce lui remontera.

## 6. Le calendrier, puis un essai à blanc
`python3 installer.py calendrier` (mardi et jeudi 10 h : 2 demandes ; chaque jour 9 h : relevé et relances ; lundi 6 h : recherche ; lundi 8 h : point). Puis `python3 installer.py essai` : montrer à l'utilisateur un mail de demande et le point tels qu'ils partiraient (aperçus dans `donnees/apercus/`). Rien n'est envoyé avant le premier passage du calendrier. `python3 installer.py etat` résume.

## 7. Contribuer à la liste commune
Lui dire en une ligne : son agent de recherche propose des courtiers chaque lundi ; ceux qu'il valide peuvent être proposés à la liste commune par une demande de fusion (voir `CONTRIBUTING.md`), avec la page source, sans aucune donnée personnelle. Un mainteneur humain les accepte après vérification.

## Changer un réglage plus tard
Relancer ce skill : chaque étape se refait seule (`installer.py` remplace l'ancien réglage).
