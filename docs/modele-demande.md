# Modèles de mail

Les champs entre accolades sont remplis depuis `donnees/identite.json`, hors du dépôt. Le texte qui part est celui de `effacement/agent.py` ; ce document le montre en clair.

## 1. La demande (et sa relance)
Repris du modèle officiel de la CNIL. La relance, un mois plus tard, reprend le même texte précédé d'une phrase qui rappelle la date de la première demande.

**Objet** : Demande d'effacement de données personnelles (article 17 du RGPD)

Madame, Monsieur,

En application de l'article 17.1 du Règlement général sur la protection des données (RGPD), je vous prie d'effacer de vos fichiers les données personnelles suivantes me concernant : {donnees_a_effacer} (nom, adresses électroniques, numéro de téléphone, adresses postales, ainsi que toute donnée qui y est rattachée).

Je demande que ces informations soient supprimées car je retire tout consentement que j'aurais pu donner à leur traitement (article 17.1.b) et je m'oppose à leur utilisation à des fins de prospection (articles 21.2 et 17.1.c du RGPD).

Vous voudrez bien également notifier cette demande d'effacement aux organismes auxquels vous les auriez communiquées (article 19 du RGPD).

Je vous prie de m'informer de ces éléments dans les meilleurs délais et au plus tard dans un délai d'un mois à compter de la réception de ce courrier (article 12.3 du RGPD). À défaut de réponse dans ce délai ou en cas de réponse incomplète, je saisirai la Commission nationale de l'informatique et des libertés (CNIL) d'une réclamation.

Je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées.

{prenom} {nom}

## 2. Le courtier renvoie vers son formulaire
Le projet n'utilise que le mail. Réponse envoyée une fois :

> Vous m'invitez à passer par votre formulaire. Ma demande d'effacement du {date} a été adressée à l'adresse que vous publiez pour l'exercice des droits : elle est valable telle quelle.
>
> Le RGPD n'impose aucune forme à une demande, et la personne concernée n'est pas tenue d'utiliser le canal que vous préférez : une demande faite par un autre canal fourni par l'organisme est en général effective et doit être traitée (Comité européen de la protection des données, lignes directrices 01/2022, points 52 et 53 ; article 12.2 du RGPD).
>
> Je vous remercie donc de traiter ma demande dans le délai d'un mois à compter de sa réception (article 12.3 du RGPD). À défaut, je saisirai la CNIL d'une réclamation.

## 3. Le courtier demande une pièce d'identité
Seulement si la demande est authentifiée (voir `SECURITY.md`) ; copie filigranée jointe :

> Suite à votre message, vous trouverez ci-joint une copie de ma pièce d'identité, portant un filigrane qui en limite l'usage, afin de vérifier mon identité pour ma demande d'effacement (article 12.6 du RGPD). Cette copie ne peut servir qu'à cette vérification : je vous demande de la supprimer dès la vérification faite, et de me confirmer l'effacement de mes données dans le délai prévu à l'article 12.3.

## 4. La plainte à la CNIL
Préparée par l'agent (`donnees/cnil/`), déposée par l'utilisateur sur https://www.cnil.fr/fr/plaintes : le texte rappelle l'organisme, les dates de la demande et de la relance, l'absence de réponse au-delà du délai d'un mois, et liste les pièces numérotées.
