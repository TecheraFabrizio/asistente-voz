@echo off
rem One click: mic listener + panel + Claude Code already watching the voice file.
rem Needs Claude Code installed and logged in (run "claude" once by hand the first time).
cd /d "%~dp0"
start "voice listener" /min python voz\escucha.py
start "" pythonw voz\panel.py
claude "Watch voz/entrada.txt with a Monitor (tail -n0 -F; re-arm it whenever it expires). Each new line is a voice request from me: act on it. Write every reply to voz/ultima_respuesta.txt, copy it to voz/respuesta.txt so the panel shows it, and write a short spoken version to voz/narracion.txt. Answer in the language set in voz/config.json."
