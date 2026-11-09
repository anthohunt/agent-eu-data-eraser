#!/bin/sh
# Lance une commande de l'agent (appelé par cron) ; trace dans donnees/cron.log.
# Usage : ./lancer.sh envoyer --n 2 | relever | relancer | point
ICI=$(cd "$(dirname "$0")" && pwd)
PY="$ICI/.venv/bin/python"; [ -x "$PY" ] || PY=python3
cd "$ICI/effacement" && "$PY" -I agent.py "$@" >> "$ICI/donnees/cron.log" 2>&1
