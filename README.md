# Voice assistant for Claude Code

**English** · [Español más abajo](#asistente-de-voz-para-claude-code)

Talk to Claude Code without touching the keyboard. Whisper transcribes locally on the GPU, Claude fixes the transcript from context and acts.
On-screen status panel with live steps, a formatted answer panel, spoken narration, and step-by-step guided tours with arrows and labels drawn over any application.

Default language is Spanish. Switch to English with one click on the panel. Voice commands are accepted in both languages at all times.

## What you get

- **Wake word, no keys.** Say `go` (or `va`), speak, say `done`. The request lands in Claude Code.
- **Status panel.** Shows whether it is idle, recording or transcribing, what you dictated, and every step Claude takes, in real time.
- **Answer panel.** Claude's reply, formatted (headings, bullets, bold), attached above the status panel. Scrollable, collapsible, slightly transparent.
- **Narration.** Say `narrate` and the answer is read aloud with a natural neural voice. Say `go` or `shut up` to stop it.
- **Guided tours.** Claude draws arrows, boxes and labels over any window, narrates each step, erases it and moves to the next. Click-through: you keep using the app underneath.
- **Language toggle.** `ES | EN` on the panel switches transcription, voice and UI strings live.

## Setup

```
pip install -r requirements.txt
python voz/config.py en        # or: es  (default)
python voz/escucha.py          # mic listener (GPU)
pythonw voz/panel.py           # status + answer panel
```

In Claude Code, watch `voz/entrada.txt` (Monitor with `tail -n0 -F`). Each line is a voice request.
The hooks in `.claude/settings.json` push every tool call to the panel and say "done" when a voice request finishes. Paths are relative to the project folder.

Claude writes its reply to `voz/ultima_respuesta.txt` (and copies it to `voz/respuesta.txt` to show it), and a spoken version to `voz/narracion.txt`.

## Voice commands

| say (en) | decís (es) | what happens |
|---|---|---|
| `go` … `done` | `va` … `listo` | dictate a request and send it |
| `go` again | `va` de nuevo | clear and restart the dictation |
| `cancel` | `cancelá` | drop the dictation |
| `show answer` / `close` | `ver respuesta` / `cerralo` | open / close the answer panel |
| `narrate` | `narralo` | read the answer out loud |
| `shut up` | `callate` | stop the voice |
| `clear arrows` | `borrá las flechas` | remove drawings |

## Guided tours

A tour is a JSON file with steps. Each step has overlay items (box, arrow, label, numbered circle) and the text to narrate:

```
python voz/tour.py voz/tour_ejemplo.json
```

See `voz/tour_ejemplo.json`. Coordinates are pixels on the monitor given by `x`, `y`, `w`, `h`.

## Files

- `voz/config.py` language (`config.json`), voice and UI strings
- `voz/escucha.py` mic → Whisper → `entrada.txt`, voice commands, speech queue
- `voz/panel.py` status panel and answer panel
- `voz/hablar.py` text to speech, sentence by sentence (edge-tts)
- `voz/tour.py` guided tour runner: draw, narrate, erase, next
- `voz/hook_paso.py` Claude Code hook that feeds the panel
- `overlay.py` click-through arrows and labels over the screen
- `voz/tour_ejemplo.json` example tour

Requires Windows, Python 3.11+, an NVIDIA GPU for Whisper (CPU works, slower) and internet for the neural voice (falls back to the Windows voice offline).

---

# Asistente de voz para Claude Code

Le hablás a Claude Code sin tocar el teclado. Whisper transcribe local en la GPU, Claude corrige con contexto y actúa.
Panel de estado con los pasos en vivo, panel de respuesta formateado, narración en voz alta y recorridos guiados con flechas y carteles sobre cualquier aplicación.

Idioma por defecto: español. Se pasa a inglés con un click en el panel. Los comandos de voz se aceptan en los dos idiomas siempre.

## Qué hace

- **Palabra de activación, sin teclas.** Decís `va`, hablás, decís `listo`. La orden llega a Claude Code.
- **Panel de estado.** Muestra si está en espera, grabando o transcribiendo, lo que dictaste, y cada paso que Claude ejecuta, en tiempo real.
- **Panel de respuesta.** La respuesta de Claude formateada (títulos, viñetas, negritas), pegada arriba del panel. Con scroll, colapsable, un poco transparente.
- **Narración.** Decís `narralo` y la respuesta se lee con una voz neuronal natural. `va` o `callate` la cortan.
- **Recorridos guiados.** Claude dibuja flechas, recuadros y carteles sobre cualquier ventana, narra cada paso, lo borra y sigue. Los clicks atraviesan el dibujo.
- **Idioma.** `ES | EN` en el panel cambia transcripción, voz y textos en vivo.

## Arranque

```
pip install -r requirements.txt
python voz/config.py es        # o: en
python voz/escucha.py          # escucha el mic (GPU)
pythonw voz/panel.py           # panel de estado y respuesta
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

## Recorridos guiados

Un recorrido es un JSON con pasos. Cada paso tiene los dibujos (recuadro, flecha, cartel, número) y el texto que se narra:

```
python voz/tour.py voz/tour_ejemplo.json
```

Ver `voz/tour_ejemplo.json`. Las coordenadas son píxeles del monitor indicado por `x`, `y`, `w`, `h`.

## Archivos

- `voz/config.py` idioma (`config.json`), voz y textos
- `voz/escucha.py` mic → Whisper → `entrada.txt`, comandos de voz, cola de habla
- `voz/panel.py` panel de estado y de respuesta
- `voz/hablar.py` texto a voz, frase por frase (edge-tts)
- `voz/tour.py` recorrido guiado: dibuja, narra, borra, sigue
- `voz/hook_paso.py` hook de Claude Code que alimenta el panel
- `overlay.py` flechas y carteles click-through sobre la pantalla
- `voz/tour_ejemplo.json` recorrido de ejemplo

Requiere Windows, Python 3.11+, GPU NVIDIA para Whisper (en CPU anda, más lento) e internet para la voz neuronal (sin internet usa la voz de Windows).
