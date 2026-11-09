# Sécurité et vie privée

## Ce qui est gardé, et où
Tout ce qui est personnel reste sur la machine de l'utilisateur, dans `donnees/` (ignoré par git, droits 700/600) : éléments à effacer, accès à la boîte d'envoi, pièce d'identité éventuelle, journal, copies des mails envoyés et reçus, dossiers de plainte. Le dépôt ne contient que le code, les modèles et la liste publique des courtiers.

## Les risques pris en compte
- **Un faux courtier dans la liste** : il recevrait nom, mails, téléphone et adresses de chaque utilisateur. Parade : une adresse n'entre dans la liste commune qu'avec la page de son propre domaine qui la publie, acceptée par un mainteneur humain ; chaque utilisateur valide en plus toute nouvelle adresse avant que son agent y écrive.
- **Un faux mail « du courtier » qui réclame la pièce d'identité** : l'agent ne répond qu'à une demande signée (DKIM) par un domaine du courtier, seulement à l'adresse validée de la liste (jamais à l'adresse de la demande), une fois par courtier, avec une copie barrée d'un filigrane « Demande RGPD à <courtier>, <date>, usage unique ». Sans pièce fournie, la demande remonte à l'utilisateur.
- **Un lien piégé** : l'agent ne suit un lien de confirmation que si le mail est authentifié pour le domaine du courtier.
- **Une page web qui donne des ordres à l'agent de recherche** : sa consigne traite tout texte lu comme une donnée, jamais comme une instruction ; il ne fait que proposer et n'envoie rien.
- **L'accès à la boîte** : un mot de passe d'application réservé à l'agent ; le supprimer chez le fournisseur coupe l'agent sans toucher au reste.

## Signaler un problème
Ouvrir un ticket sans y mettre aucune donnée personnelle, ou, pour une faille, écrire au mainteneur par le contact indiqué sur la page GitHub du projet.
