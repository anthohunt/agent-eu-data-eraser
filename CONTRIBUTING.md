# Contribuer à la liste des courtiers

La valeur de ce projet tient surtout à sa liste : quels courtiers en données existent, et comment chacun accepte une demande d'effacement. Toute personne peut l'enrichir.

## Ajouter ou corriger un courtier
Modifier `effacement/courtiers.json` (une entrée par courtier), régénérer la liste lisible (`python3 outils/liste.py`), et ouvrir une demande de fusion (pull request) avec :

```json
{"id": "exemple", "nom": "Exemple SAS", "canal": "mail", "adresse": "dpo@exemple.fr",
 "domaines": ["exemple.fr"], "pays": ["FR"], "source": "https://exemple.fr/confidentialite", "vu_le": "2026-11-09"}
```

- `canal` : toujours `mail` ; `adresse` : celle du délégué à la protection des données ou du service vie privée, publiée sur le site du courtier lui-même. Un courtier qui n'a qu'un formulaire n'est pas ajouté.
- `domaines` : les domaines d'où viennent les réponses du courtier (sert à les reconnaître dans la boîte). Jamais celui d'un prestataire partagé (OneTrust, TrustArc…) : pour un courtier qui répond par l'un d'eux, `expediteurs` (un mot du nom affiché de l'expéditeur) ou `objets` (un mot de l'objet).
- `source` et `vu_le` : la page où l'adresse est publiée, et la date de lecture. Une entrée sans source n'est pas acceptée.

## Règles
- Seulement des adresses publiées par le courtier lui-même.
- Aucune donnée personnelle dans une contribution (ni nom, ni adresse, ni capture de demande).
- Un courtier fermé ou sans adresse : dans `effacement/courtiers.json`, passer `canal` à `aucun` et expliquer dans `note`, avec la preuve en `source`, plutôt que le supprimer ; puis régénérer la liste.

## Validation
Un mainteneur humain accepte chaque ajout après avoir vérifié que l'adresse figure bien sur la page source, sur le domaine du courtier. Pas de vote automatique : un faux courtier accepté en masse recevrait les données de tous les utilisateurs (voir `SECURITY.md`).
