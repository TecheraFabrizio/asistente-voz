# Voice assistant for Claude Code

**English** · [Español más abajo](#asistente-de-voz-para-claude-code)

Talk to Claude Code without touching the keyboard. Whisper transcribes locally on the GPU, Claude fixes the transcript from context and acts.
On-screen status panel with live steps, a formatted answer panel, spoken narration, and step-by-step guided tours with arrows and labels drawn over any application.

Default language is English. Switch to Spanish with one click on the panel. Voice commands are accepted in both languages at all times, and dictation is language-agnostic: Whisper detects whether you spoke Spanish or English and writes it in that language.

## What you get

- **Wake word, no keys.** Say `go` (or `va`), speak, say `done`. The request lands in Claude Code.
- **Edit before sending.** Click the dictation box and fix the transcript by hand. What is in the box is what gets sent: say `done` or press **Enter**. **Esc** releases the box.
- **Status panel.** Shows whether it is idle, recording or transcribing, what you dictated, and every step Claude takes, in real time.
- **Answer panel.** Claude's reply, formatted (headings, bullets, bold), attached above the status panel. Scrollable, collapsible, slightly transparent.
- **Narration.** Say `narrate` and the answer is read aloud with a natural neural voice. Say `go` or `quiet` to stop it.
- **Guided tours.** Claude draws arrows, boxes and labels over any window, narrates each step, erases it and moves to the next. Click-through: you keep using the app underneath.
- **Language toggle.** `ES | EN` on the panel switches transcription, voice and UI strings live.
- **Animated character.** Rover (the Windows XP search dog), Merlin the wizard or Clippy lives on the panel: searches and writes while Claude works, celebrates when done, rests when idle. Left-click it for a random interaction, right-click to switch character. Sprites from the open-source clippy.js project (MIT).

## Setup

After `pip install -r requirements.txt`, one command starts everything (listener, panel and Claude Code already watching the voice file):

```
start.bat        # Windows
./start.sh       # Linux / macOS
```

No IDE needed: Claude Code runs in that terminal. VS Code is optional.

The scripts start Claude Code with `--dangerously-skip-permissions`, so nothing stops to ask for permission: that is what makes it hands-free. It also means Claude can run any command on that machine without asking. If you want prompts, remove the flag, or use `--permission-mode acceptEdits` plus an allow list in `.claude/settings.json`.

By hand:

```
pip install -r requirements.txt
python voz/config.py en        # default. or: es
python voz/escucha.py          # mic listener (GPU)
pythonw voz/panel.py           # status + answer panel (Linux/Mac: python voz/panel.py &)
```

In Claude Code, watch `voz/entrada.txt` (Monitor with `tail -n0 -F`). Each line is a voice request.
The hooks in `.claude/settings.json` push every tool call to the panel and say "done" when a voice request finishes. Paths are relative to the project folder.

Claude writes its reply to `voz/ultima_respuesta.txt` (and copies it to `voz/respuesta.txt` to show it), and a spoken version to `voz/narracion.txt`.

## Voice commands

| say (en) | decís (es) | what happens |
|---|---|---|
| `go` … `done` | `va` … `listo` | dictate a request and send it |
| **Enter** in the box | **Enter** en la caja | send what is in the box: typed or dictated, no `go` needed |
| `go` again | **Enter** en la caja | manda lo que hay en la caja: tipeado o dictado, sin decir `va` |
| `va` de nuevo | clear and restart the dictation |
| `cancel` | `cancelá` | drop the dictation |
| `show answer` / `close` | `ver respuesta` / `cerralo` | open / close the answer panel |
| `narrate` | `narralo` | read the answer out loud |
| `quiet` / `stop` | `callate` | stop the voice |
| `clear arrows` | `borrá las flechas` | remove drawings |
| `assistant hide` / `assistant show` | `asistente ocultar` / `asistente mostrar` | hide or show the panel (the listener keeps running) |

## Guided tours

A tour is a JSON file with steps. Each step has overlay items (box, arrow, label, numbered circle) and the text to narrate:

```
python voz/tour.py voz/tour_ejemplo.json
```

See `voz/tour_ejemplo.json`. Coordinates are pixels on the monitor given by `x`, `y`, `w`, `h`.

See `CHANGELOG.md` for everything done so far.

## Files

- `voz/config.py` language (`config.json`), voice and UI strings
- `voz/escucha.py` mic → Whisper → `entrada.txt`, voice commands, speech queue
- `voz/panel.py` status panel and answer panel
- `voz/hablar.py` text to speech, sentence by sentence (edge-tts)
- `voz/tour.py` guided tour runner: draw, narrate, erase, next
- `voz/hook_paso.py` Claude Code hook that feeds the panel
- `overlay.py` click-through arrows and labels over the screen
- `voz/agente.py` animated character (Rover / Merlin / Clippy)
- `voz/so.py` OS-specific bits: beep, processes, audio playback, offline voice, CUDA
- `voz/tour_ejemplo.json` example tour

## Platforms

Works on **Windows, Linux and macOS**. Python 3.11+. Everything OS-specific lives in `voz/so.py`.

- **GPU:** NVIDIA on Windows/Linux (CUDA libraries come with `pip install`). Without one, or on a Mac, Whisper runs on CPU: 2 to 4 s per sentence instead of under 1 s.
- **Audio playback:** Windows uses .NET, macOS uses `afplay`, Linux needs `ffmpeg` (ffplay) or `mpv` installed.
- **Offline voice** (no internet): Windows SAPI, macOS `say`, Linux `spd-say` or `espeak-ng`.
- **Click-through overlays** (clicks pass through the drawings) are Windows-only. On Linux/macOS the drawings show the same but block clicks until you say `clear arrows`.
- **Hooks** call `python` and fall back to `python3`.

Tested on Windows 11. Linux and macOS support is written against the platform APIs but has not been run on those systems yet; please report issues.

---

# Asistente de voz para Claude Code

Le hablás a Claude Code sin tocar el teclado. Whisper transcribe local en la GPU, Claude corrige con contexto y actúa.
Panel de estado con los pasos en vivo, panel de respuesta formateado, narración en voz alta y recorridos guiados con flechas y carteles sobre cualquier aplicación.

Idioma por defecto: inglés. Se pasa a español con un click en el panel. Los comandos de voz se aceptan en los dos idiomas siempre, y el dictado es mixto: Whisper detecta si hablaste en español o en inglés y lo escribe en ese idioma.

## Qué hace

- **Palabra de activación, sin teclas.** Decís `va`, hablás, decís `listo`. La orden llega a Claude Code.
- **Corregir antes de mandar.** Click en la caja de dictado y arreglás el texto a mano. Lo que queda en la caja es lo que se manda: decís `listo` o apretás **Enter**. **Esc** suelta la caja.
- **Panel de estado.** Muestra si está en espera, grabando o transcribiendo, lo que dictaste, y cada paso que Claude ejecuta, en tiempo real.
- **Panel de respuesta.** La respuesta de Claude formateada (títulos, viñetas, negritas), pegada arriba del panel. Con scroll, colapsable, un poco transparente.
- **Narración.** Decís `narralo` y la respuesta se lee con una voz neuronal natural. `va` o `callate` la cortan.
- **Recorridos guiados.** Claude dibuja flechas, recuadros y carteles sobre cualquier ventana, narra cada paso, lo borra y sigue. Los clicks atraviesan el dibujo.
- **Idioma.** `ES | EN` en el panel cambia transcripción, voz y textos en vivo.
- **Personaje animado.** Rover (el perrito de la búsqueda de Windows XP), Merlin el mago o Clippy viven en el panel: buscan y escriben mientras Claude trabaja, festejan al terminar, descansan en espera. Click izquierdo: una interacción al azar. Click derecho: cambia de personaje. Sprites del proyecto abierto clippy.js (MIT).

## Arranque

Después de `pip install -r requirements.txt`, un solo comando arranca todo (escucha, panel y Claude Code ya vigilando el archivo de voz):

```
start.bat        # Windows
./start.sh       # Linux / macOS
```

No hace falta IDE: Claude Code corre en esa terminal. VS Code es opcional.

Los scripts arrancan Claude Code con `--dangerously-skip-permissions`, así nada se frena a pedir permiso: eso es lo que lo hace manos libres. También significa que Claude puede correr cualquier comando en esa máquina sin preguntar. Si preferís que pregunte, sacá la opción, o usá `--permission-mode acceptEdits` más una lista de permitidos en `.claude/settings.json`.

A mano:

```
pip install -r requirements.txt
python voz/config.py es        # el default es en
python voz/escucha.py          # escucha el mic (GPU)
pythonw voz/panel.py           # panel de estado y respuesta (Linux/Mac: python voz/panel.py &)
```

En Claude Code, vigilar `voz/entrada.txt` (Monitor con `tail -n0 -F`). Cada línea es una orden de voz.
Los hooks de `.claude/settings.json` mandan cada herramienta al panel y dicen "listo" al terminar una orden. Las rutas son relativas a la carpeta del proyecto.

Claude escribe su respuesta en `voz/ultima_respuesta.txt` (y la copia a `voz/respuesta.txt` para mostrarla), y una versión hablada en `voz/narracion.txt`.

## Palabras clave

| decís | pasa |
|---|---|
| `va` … `listo` | dicta una orden y la manda |
| `va` de nuevo | borra lo dictado y empieza de cero |
| `cancelá` | tira el dictado |
| `ver respuesta` / `cerralo` | abre y cierra el panel de respuesta |
| `narralo` | lee la respuesta en voz alta |
| `callate` | corta la voz |
| `borrá las flechas` | saca los dibujos |
| `asistente ocultar` / `asistente mostrar` | esconde o trae el panel (el escucha sigue) |

## Recorridos guiados

Un recorrido es un JSON con pasos. Cada paso tiene los dibujos (recuadro, flecha, cartel, número) y el texto que se narra:

```
python voz/tour.py voz/tour_ejemplo.json
```

Ver `voz/tour_ejemplo.json`. Las coordenadas son píxeles del monitor indicado por `x`, `y`, `w`, `h`.

En `CHANGELOG.md` está todo lo hecho hasta ahora.

## Archivos

- `voz/config.py` idioma (`config.json`), voz y textos
- `voz/escucha.py` mic → Whisper → `entrada.txt`, comandos de voz, cola de habla
- `voz/panel.py` panel de estado y de respuesta
- `voz/hablar.py` texto a voz, frase por frase (edge-tts)
- `voz/tour.py` recorrido guiado: dibuja, narra, borra, sigue
- `voz/hook_paso.py` hook de Claude Code que alimenta el panel
- `overlay.py` flechas y carteles click-through sobre la pantalla
- `voz/agente.py` personaje animado (Rover / Merlin / Clippy)
- `voz/so.py` lo que depende del sistema: beep, procesos, audio, voz sin internet, CUDA
- `voz/tour_ejemplo.json` recorrido de ejemplo

## Plataformas

Anda en **Windows, Linux y macOS**. Python 3.11 o más nuevo. Todo lo que depende del sistema está en `voz/so.py`.

- **GPU:** NVIDIA en Windows/Linux (las librerías de CUDA vienen con el `pip install`). Sin GPU, o en Mac, Whisper corre en CPU: 2 a 4 s por frase en vez de menos de 1 s.
- **Audio:** Windows usa .NET, macOS usa `afplay`, Linux necesita `ffmpeg` (ffplay) o `mpv` instalado.
- **Voz sin internet:** Windows SAPI, macOS `say`, Linux `spd-say` o `espeak-ng`.
- **Dibujos que dejan pasar los clicks:** sólo en Windows. En Linux/macOS se ven igual pero tapan los clicks hasta que decís `borrá las flechas`.
- **Hooks:** llaman a `python` y si no existe, a `python3`.

Probado en Windows 11. Linux y macOS están escritos contra las APIs de cada sistema pero todavía no se corrieron ahí; si algo falla, avisá.
