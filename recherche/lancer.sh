#!/bin/sh
# Lance une passe de l'agent de recherche (appelé chaque semaine par le calendrier).
# Par défaut : Claude Code en mode non interactif. Une machine qui lance ses agents autrement met son propre
# lanceur dans donnees/lancer-recherche.local (hors dépôt) ; il reçoit le dossier du dépôt en argument.
PATH="/usr/local/bin:$HOME/.local/bin:$PATH"; export PATH
ICI=$(cd "$(dirname "$0")/.." && pwd)
[ -x "$ICI/donnees/lancer-recherche.local" ] && exec "$ICI/donnees/lancer-recherche.local" "$ICI" "$@"
[ "$1" = "--essai" ] && { echo "lanceur : claude -p"; exit 0; }
cd "$ICI" && claude -p --dangerously-skip-permissions < recherche/consigne.md >> "$ICI/donnees/recherche.log" 2>&1
