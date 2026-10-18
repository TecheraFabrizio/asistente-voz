# Hook de Claude Code: anota en voz/accion.txt cada accion que Claude ejecuta.
# Asi el panel muestra en tiempo real que esta haciendo, sin depender de que Claude lo escriba.
#
# Lo llama Claude Code con el evento por argumento:
#   pre     -> antes de cada herramienta: agrega un paso
#   stop    -> cuando Claude termina de responder: limpia los pasos
#   prompt  -> cuando llega una orden nueva: arranca con "procesando tu orden"

import sys, json, os
from pathlib import Path

ACCION = Path(__file__).parent / "accion.txt"
MAX = 6     # cuantos pasos guardo
sys.path.insert(0, str(Path(__file__).parent))
import config as CFG

def nombre(p):
    return os.path.basename(str(p)) if p else ""

def paso_de(tool, inp):
    # arma una linea corta y en castellano segun la herramienta
    d = inp.get("description") or ""
    if tool in ("Bash", "PowerShell"):
        return d or CFG.t("p_comando")
    if tool == "Edit":
        return CFG.t("p_editar") + nombre(inp.get("file_path"))
    if tool == "Write":
        return CFG.t("p_escribir") + nombre(inp.get("file_path"))
    if tool == "Read":
        return CFG.t("p_leer") + nombre(inp.get("file_path"))
    if tool in ("Grep", "Glob"):
        return CFG.t("p_buscar") + str(inp.get("pattern", ""))[:40]
    if tool == "Agent":
        return CFG.t("p_agente") + str(inp.get("description", ""))[:50]
    if tool == "Monitor":
        return CFG.t("p_vigilar") + str(inp.get("description", ""))[:50]
    if tool in ("WebSearch", "WebFetch"):
        return CFG.t("p_web")
    if tool.startswith("mcp__claude-in-chrome"):
        return CFG.t("p_chrome")
    return d or tool.lower()

def main():
    ev = sys.argv[1] if len(sys.argv) > 1 else "pre"
    try:
        sys.stdin.reconfigure(encoding="utf-8")   # claude manda utf-8; windows asume cp1252
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    if ev == "stop":
        ACCION.write_text("", encoding="utf-8")
        # si la orden vino por voz, avisa hablando que termino
        flag = ACCION.parent / "orden_pendiente"
        if flag.exists():
            try:
                flag.unlink()
            except Exception:
                pass
            # lo dice el escucha (asi no se escucha a si mismo): le dejo el texto en hablar.txt
            (ACCION.parent / "hablar.txt").write_text(CFG.t("listo"), encoding="utf-8")
        return
    if ev == "prompt":
        ACCION.write_text(CFG.t("procesando") + "\n", encoding="utf-8")
        return
    paso = paso_de(data.get("tool_name", ""), data.get("tool_input", {}) or {})
    try:
        lineas = ACCION.read_text(encoding="utf-8").splitlines()
    except Exception:
        lineas = []
    lineas = [l for l in lineas if l.strip()]
    if not lineas or lineas[-1] != paso:
        lineas.append(paso)
    ACCION.write_text("\n".join(lineas[-MAX:]) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
