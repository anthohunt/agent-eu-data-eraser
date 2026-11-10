#!/bin/sh
# Lance une commande de l'agent (appelé par cron) ; trace dans donnees/cron.log.
# Usage : ./lancer.sh envoyer --n 2 | relever | relancer | point | tri trier | tri purger
# Le tri des spams appelle un modèle d'IA : son réglage propre à la machine (compte, jeton) est lu dans
# donnees/lancer-recherche.local, comme pour l'agent de recherche.
ICI=$(cd "$(dirname "$0")" && pwd)
PY="$ICI/.venv/bin/python"; [ -x "$PY" ] || PY=python3
SCRIPT=agent.py
if [ "$1" = "tri" ]; then
  shift; SCRIPT=tri.py
  PATH="/usr/local/bin:$HOME/.local/bin:$PATH"; export PATH
  [ -f "$ICI/donnees/lancer-recherche.local" ] && . "$ICI/donnees/lancer-recherche.local"
fi
cd "$ICI/effacement" && "$PY" -I "$SCRIPT" "$@" >> "$ICI/donnees/cron.log" 2>&1
