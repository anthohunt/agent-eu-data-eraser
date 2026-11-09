#!/usr/bin/env python3
"""Régénère docs/courtiers.md depuis effacement/courtiers.json (la liste lisible par un humain)."""
import json
from pathlib import Path
R = Path(__file__).resolve().parent.parent
L = json.loads((R / "effacement" / "courtiers.json").read_text(encoding="utf-8"))
mail = sorted((c for c in L if c.get("canal") == "mail" and c.get("adresse")), key=lambda c: c["nom"].lower())
sans = sorted((c for c in L if not (c.get("canal") == "mail" and c.get("adresse"))), key=lambda c: c["nom"].lower())
o = ["# Liste des courtiers", "",
     "Générée depuis `effacement/courtiers.json` par `outils/liste.py` ; ne pas modifier à la main.", "",
     f"**{len(mail)} courtiers joignables par mail.** Chaque adresse est celle que le courtier publie lui-même pour les "
     "demandes RGPD ; la page source et sa date de lecture sont indiquées.", "",
     "| Courtier | Pays | Adresse | Source | Vu le |", "|---|---|---|---|---|"]
for c in mail:
    pays = ", ".join(c.get("pays", [])) if isinstance(c.get("pays"), list) else c.get("pays", "")
    src = f"[page]({c['source']})" if c.get("source") else ""
    o.append(f"| {c['nom']} | {pays} | `{c['adresse']}` | {src} | {c.get('vu_le', '')} |")
if sans:
    o += ["", f"**{len(sans)} sans adresse mail connue** : l'agent ne leur écrit pas tant qu'une adresse publiée n'a pas été trouvée.", ""]
    o += [f"- {c['nom']}" for c in sans]
(R / "docs" / "courtiers.md").write_text("\n".join(o) + "\n", encoding="utf-8")
print(f"{len(mail)} par mail, {len(sans)} sans adresse")

# Autorités de protection des données (une par pays), pour la plainte
A = json.loads((R / "effacement" / "autorites.json").read_text(encoding="utf-8"))
o = ["# Data protection authorities / Autorités de protection des données", "",
     "Generated from `effacement/autorites.json` by `outils/liste.py`. The agent names the user's own authority in its "
     "emails and prepares the complaint for it. / Généré par `outils/liste.py` ; l'agent cite l'autorité du pays de "
     "l'utilisateur et prépare la plainte pour elle.", "",
     "| | Authority | Complaint page | Notes |", "|---|---|---|---|"]
for a in A:
    url = f"[link]({a['plainte_url']})" if a.get("plainte_url") else "—"
    notes = (a.get("plainte_notes") or "").replace("|", "/").replace("\n", " ")[:160]
    o.append(f"| {a['pays']} | {a.get('autorite_en') or a['autorite']} | {url} | {notes} |")
(R / "docs" / "autorites.md").write_text("\n".join(o) + "\n", encoding="utf-8")
print(f"{len(A)} autorités")
