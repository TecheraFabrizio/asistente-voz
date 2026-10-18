#!/bin/sh
# One command: mic listener + panel + Claude Code already watching the voice file.
# Needs Claude Code installed and logged in (run "claude" once by hand the first time).
cd "$(dirname "$0")"
PY=$(command -v python3 || command -v python)
"$PY" voz/escucha.py > voz/escucha.log 2>&1 &
"$PY" voz/panel.py > /dev/null 2>&1 &
# --dangerously-skip-permissions: no permission prompts, so it works hands-free by voice.
# It means Claude can run any command without asking. Remove the flag if you prefer prompts.
claude --dangerously-skip-permissions "Watch voz/entrada.txt with a Monitor (tail -n0 -F; re-arm it whenever it expires). Each new line is a voice request from me: act on it. Write every reply to voz/ultima_respuesta.txt, copy it to voz/respuesta.txt so the panel shows it, and write a short spoken version to voz/narracion.txt. Answer in the language set in voz/config.json."
