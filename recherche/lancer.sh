#!/bin/sh
# Lance une passe de l'agent de recherche (chaque semaine, par le calendrier).
# L'agent lit des pages web non fiables : il tourne dans un dossier temporaire qui ne contient QUE la liste publique
# (jamais donnees/), avec des outils limités (recherche et lecture web, lecture de ce dossier, écriture du seul
# fichier de propositions) et sans Bash. Le fichier rendu est vérifié avant d'être recopié dans le dépôt.
# Une machine peut régler l'environnement de Claude (compte, jeton) dans donnees/lancer-recherche.local, lu ici.
PATH="/usr/local/bin:$HOME/.local/bin:$PATH"; export PATH
ICI=$(cd "$(dirname "$0")/.." && pwd)
[ -f "$ICI/donnees/lancer-recherche.local" ] && . "$ICI/donnees/lancer-recherche.local"
[ "$1" = "--essai" ] && { echo "bac à sable prêt ; outil : ${RECHERCHE_CMD:-claude ($(command -v claude || echo absent))}"; exit 0; }
T=$(mktemp -d) || exit 1
trap 'rm -rf "$T"' EXIT
mkdir -p "$T/effacement" "$T/docs" && cp "$ICI/README.md" "$ICI/CONTRIBUTING.md" "$T/" \
  && cp "$ICI/effacement/courtiers.json" "$T/effacement/" \
  && cp "$ICI/recherche/consigne.md" "$T/consigne.md" || exit 1
# passe ciblée (facultatif) : FOCUS="Allemagne" sh recherche/lancer.sh
[ -n "$FOCUS" ] && printf '\nCette passe : concentre-toi sur les courtiers actifs en %s (sources de son autorité de protection des données, annuaires, politiques en langue locale).\n' "$FOCUS" >> "$T/consigne.md"
# les propositions sont propres à l'utilisateur : elles vivent dans donnees/, hors dépôt
P="$ICI/donnees/courtiers-proposes.json"
[ -f "$P" ] || printf '{"a_valider": [], "corrections": []}\n' > "$P"
cp "$P" "$T/docs/courtiers-proposes.json"
# l'agent connaît aussi les courtiers déjà validés par l'utilisateur, pour ne pas les reproposer
[ -f "$ICI/donnees/courtiers-ajoutes.json" ] && cp "$ICI/donnees/courtiers-ajoutes.json" "$T/effacement/courtiers-ajoutes.json"
# L'outil d'IA est réglable : RECHERCHE_CMD = une commande qui lit la consigne sur son entrée, travaille dans le dossier
# courant et modifie docs/courtiers-proposes.json. Par défaut, Claude Code avec des outils limités (pas de shell).
# Avec un autre outil, lui donner les mêmes limites : recherche web, lecture du dossier, écriture de ce seul fichier.
if [ -n "$RECHERCHE_CMD" ]; then
  ( cd "$T" && sh -c "$RECHERCHE_CMD" < consigne.md ) >> "$ICI/donnees/recherche.log" 2>&1
else
  ( cd "$T" && claude -p --allowedTools "WebSearch" "WebFetch" "Read(/**)" "Edit(/docs/courtiers-proposes.json)" --disallowedTools "Bash" \
      < consigne.md ) >> "$ICI/donnees/recherche.log" 2>&1
fi
cp "$T/docs/courtiers-proposes.json" "$ICI/donnees/recherche-derniere-sortie.json" 2>/dev/null
python3 - "$T/docs/courtiers-proposes.json" "$P" <<'PY' >> "$ICI/donnees/recherche.log" 2>&1 || exit 1
import json, re, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
garde = {"a_valider": [], "corrections": []}
def domaine_ok(adresse, domaines):
    dom = adresse.rsplit("@", 1)[-1].lower()
    return any(dom == k.lower() or dom.endswith("." + k.lower()) for k in domaines)
for x in d.get("a_valider", []):  # chaque proposition est contrôlée seule : une mauvaise ne fait pas tomber les autres
    a = str(x.get("adresse", "")).strip()
    raison = ("adresse invalide" if not re.fullmatch(r"[^@\s,;]+@[a-z0-9.-]+\.[a-z]{2,}", a.lower()) else
              "source non https" if not str(x.get("source", "")).startswith("https://") else
              "adresse hors des domaines du courtier" if not domaine_ok(a, x.get("domaines", [])) else None)
    if raison:
        print(f"écartée : {x.get('id')} ({raison})")
    else:
        garde["a_valider"].append({**x, "adresse": a})
for x in d.get("corrections", []):
    if re.fullmatch(r"[^@\s,;]+@[a-z0-9.-]+\.[a-z]{2,}", str(x.get("nouvelle", "")).lower()) and str(x.get("source", "")).startswith("https://"):
        garde["corrections"].append(x)
    else:
        print(f"correction écartée : {x.get('id')}")
json.dump(garde, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"propositions : {len(garde['a_valider'])}, corrections : {len(garde['corrections'])}")
PY
