# Idioma del asistente. Lo leen escucha, panel, hablar y el hook.
# config.json: {"lang": "en"}  o  {"lang": "es"}   (ingles por defecto)
# Cambiar: python voz/config.py en   |  python voz/config.py es

import json, sys
from pathlib import Path

ARCHIVO = Path(__file__).parent / "config.json"

def lang():
    try:
        return json.loads(ARCHIVO.read_text(encoding="utf-8")).get("lang", "en")
    except Exception:
        return "en"

def _leer():
    try:
        return json.loads(ARCHIVO.read_text(encoding="utf-8"))
    except Exception:
        return {}

def set_lang(l):
    d = _leer(); d["lang"] = l
    ARCHIVO.write_text(json.dumps(d), encoding="utf-8")

def agente():
    # personaje del panel: "Rover" (perrito), "Merlin" (mago) o "Clippy". click derecho en el panel lo cambia
    return _leer().get("agente", "Rover")

def set_agente(n):
    d = _leer(); d["agente"] = n
    ARCHIVO.write_text(json.dumps(d), encoding="utf-8")

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
        # pasos que muestra el panel mientras claude trabaja
        "p_comando": "ejecutando comando", "p_editar": "editando ", "p_escribir": "escribiendo ",
        "p_leer": "leyendo ", "p_buscar": "buscando ", "p_agente": "consultando: ", "p_vigilar": "vigilando ",
        "p_web": "buscando en la web", "p_chrome": "usando Chrome",
        "borrar_dibujos": "✕ borrar dibujos",
        # lo que dice el personaje en su globo segun el estado
        "b_grabando": "Te escucho…", "b_transcribiendo": "Anotando…", "b_dictando": "Seguí. Decí \"listo\" al terminar.",
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
        "p_comando": "running command", "p_editar": "editing ", "p_escribir": "writing ",
        "p_leer": "reading ", "p_buscar": "searching ", "p_agente": "asking: ", "p_vigilar": "watching ",
        "p_web": "searching the web", "p_chrome": "using Chrome",
        "borrar_dibujos": "✕ clear drawings",
        "b_grabando": "I'm listening…", "b_transcribiendo": "Writing it down…", "b_dictando": "Go on. Say \"done\" when finished.",
    },
}

def t(clave):
    return T.get(lang(), T["en"]).get(clave, T["en"][clave])

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("es", "en"):
        set_lang(sys.argv[1]); print("lang =", sys.argv[1])
    else:
        print("lang =", lang())
