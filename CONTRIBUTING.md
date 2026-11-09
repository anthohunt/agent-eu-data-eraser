# Contributing to the broker list

*English · [Français](CONTRIBUTING.fr.md)*

The value of this project lies mostly in its list: which data brokers exist, and the address each one publishes for erasure requests. Anyone can improve it.

## Add or fix a broker
Edit `effacement/courtiers.json` (one entry per broker), regenerate the readable list (`python3 outils/liste.py`), and open a pull request with:

```json
{"id": "example", "nom": "Example SAS", "canal": "mail", "adresse": "dpo@example.fr",
 "domaines": ["example.fr"], "pays": ["FR"], "source": "https://example.fr/privacy", "vu_le": "2026-11-09"}
```

- `canal`: always `mail`; `adresse`: the data protection officer's or privacy team's address, published on the broker's own website. A broker that only offers a web form is not added.
- `domaines`: the domains the broker's replies come from (used to recognise them in the mailbox). Never a shared provider's domain (OneTrust, TrustArc…): for a broker that replies through one, use `expediteurs` (a word of the sender's display name) or `objets` (a word of the subject).
- `source` and `vu_le`: the page where the address is published, and the date it was read. An entry without a source is not accepted.

## Rules
- Only addresses published by the broker itself.
- No personal data in a contribution (no name, address, or screenshot of a request).
- A closed broker, or one without an address: set `canal` to `aucun` and explain in `note`, with the evidence in `source`, rather than deleting it; then regenerate the list.

## Validation
A human maintainer accepts each addition after checking that the address really appears on the source page, on the broker's domain. No automatic voting: a fake broker accepted in bulk would receive every user's data (see `SECURITY.md`).
