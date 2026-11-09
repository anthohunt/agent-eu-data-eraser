#!/bin/sh
# Lance une passe de l'agent de recherche (chaque semaine, par le calendrier).
# L'agent lit des pages web non fiables : il tourne dans un dossier temporaire qui ne contient QUE la liste publique
# (jamais donnees/), avec des outils limités (recherche et lecture web, lecture de ce dossier, écriture du seul
# fichier de propositions) et sans Bash. Le fichier rendu est vérifié avant d'être recopié dans le dépôt.
# Une machine peut régler l'environnement de Claude (compte, jeton) dans donnees/lancer-recherche.local, lu ici.
PATH="/usr/local/bin:$HOME/.local/bin:$PATH"; export PATH
ICI=$(cd "$(dirname "$0")/.." && pwd)
[ -f "$ICI/donnees/lancer-recherche.local" ] && . "$ICI/donnees/lancer-recherche.local"
[ "$1" = "--essai" ] && { echo "bac à sable prêt ; claude : $(command -v claude || echo absent)"; exit 0; }
T=$(mktemp -d) || exit 1
trap 'rm -rf "$T"' EXIT
mkdir -p "$T/effacement" "$T/docs" && cp "$ICI/README.md" "$ICI/CONTRIBUTING.md" "$T/" \
  && cp "$ICI/effacement/courtiers.json" "$T/effacement/" && cp "$ICI/docs/courtiers-proposes.json" "$T/docs/" \
  && cp "$ICI/recherche/consigne.md" "$T/consigne.md" || exit 1
( cd "$T" && claude -p --allowedTools "WebSearch" "WebFetch" "Read(/**)" "Edit(/docs/courtiers-proposes.json)" --disallowedTools "Bash" \
    < consigne.md ) >> "$ICI/donnees/recherche.log" 2>&1
python3 - "$T/docs/courtiers-proposes.json" "$ICI/docs/courtiers-proposes.json" <<'PY' >> "$ICI/donnees/recherche.log" 2>&1 || exit 1
import json, re, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
assert isinstance(d.get("a_valider"), list) and isinstance(d.get("corrections"), list)
for x in d["a_valider"]:
    assert re.fullmatch(r"[^@\s]+@[a-z0-9.-]+\.[a-z]{2,}", x["adresse"].lower()) and x["source"].startswith("https://")
    dom = x["adresse"].rsplit("@", 1)[1].lower()
    assert any(dom == k or dom.endswith("." + k) for k in x["domaines"]), x["id"]
json.dump(d, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"propositions : {len(d['a_valider'])}, corrections : {len(d['corrections'])}")
PY
git -C "$ICI" commit -q -m "Propositions de l'agent de recherche" -- docs/courtiers-proposes.json 2>/dev/null || true
