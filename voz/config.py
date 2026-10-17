# Idioma del asistente. Lo leen escucha, panel, hablar y el hook.
# config.json: {"lang": "es"}  o  {"lang": "en"}
# Cambiar: python voz/config.py en   |  python voz/config.py es

import json, sys
from pathlib import Path

ARCHIVO = Path(__file__).parent / "config.json"

def lang():
    try:
        return json.loads(ARCHIVO.read_text(encoding="utf-8")).get("lang", "es")
    except Exception:
        return "es"

def _leer():
    try:
        return json.loads(ARCHIVO.read_text(encoding="utf-8"))
    except Exception:
        return {}

def set_lang(l):
    d = _leer(); d["lang"] = l
    ARCHIVO.write_text(json.dumps(d), encoding="utf-8")

def agente():
    # personaje del panel: "Rover" (perrito) o "Merlin" (mago). se cambia en config.json
    return _leer().get("agente", "Rover")

# textos que cambian con el idioma
T = {
    "es": {
        "voz": "es-UY-MateoNeural",
        "prompt_whisper": "va. va, abrí la página. listo.",
        "listo": "Listo.",
        "procesando": "procesando tu orden",
        "nada_narrar": "No tengo nada para narrar todavía.",
        "espera": "EN ESPERA  ·  decí \"va\"",
        "escuchando": "ESCUCHANDO", "grabando": "GRABANDO",
        "transcribiendo": "TRANSCRIBIENDO", "cargando": "CARGANDO",
        "titulo": "ASISTENTE PERSONAL", "respuesta": "RESPUESTA", "cerrar": "cerrar",
    },
    "en": {
        "voz": "en-US-GuyNeural",
        "prompt_whisper": "go. go, open the page. done.",
        "listo": "Done.",
        "procesando": "processing your request",
        "nada_narrar": "Nothing to narrate yet.",
        "espera": "IDLE  ·  say \"go\"",
        "escuchando": "LISTENING", "grabando": "RECORDING",
        "transcribiendo": "TRANSCRIBING", "cargando": "LOADING",
        "titulo": "PERSONAL ASSISTANT", "respuesta": "ANSWER", "cerrar": "close",
    },
}

def t(clave):
    return T.get(lang(), T["es"]).get(clave, T["es"][clave])

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("es", "en"):
        set_lang(sys.argv[1]); print("lang =", sys.argv[1])
    else:
        print("lang =", lang())
