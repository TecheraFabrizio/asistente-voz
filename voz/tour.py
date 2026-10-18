# Recorrido paso a paso: dibuja un paso, lo narra, lo borra, y sigue con el siguiente.
#
# Uso: python voz/tour.py pasos.json
# pasos.json:
# {
#   "x": 1920, "y": 0, "w": 1920, "h": 1080,         # monitor
#   "pasos": [ {"items": [...items de overlay...], "texto": "lo que se narra"}, ... ]
# }
# Mientras narra deja la marca _hablando, asi el escucha no se oye a si mismo.
# "callate" lo mata desde el escucha (pid en _tour.pid).

import sys, json, subprocess, time, os
from pathlib import Path

C = Path(__file__).parent
sys.path.insert(0, str(C))
import so as SO              # lanzar y matar procesos segun el sistema operativo
RAIZ = C.parent
FLAG = C / "_hablando"
PID = C / "_tour.pid"
PASO = C / "_paso.json"

def main():
    cfg = json.load(open(sys.argv[1], encoding="utf-8-sig"))
    PID.write_text(str(os.getpid()), encoding="utf-8")
    base = {k: cfg.get(k, d) for k, d in (("x", 1920), ("y", 0), ("w", 1920), ("h", 1080))}
    try:
        for p in cfg["pasos"]:
            PASO.write_text(json.dumps({**base, "items": p["items"]}, ensure_ascii=False), encoding="utf-8")
            ov = SO.lanzar([SO.pythonw(), str(RAIZ / "overlay.py"), str(PASO)])
            time.sleep(0.6)
            FLAG.write_text("1", encoding="utf-8")
            try:
                subprocess.run([sys.executable, str(C / "hablar.py"), "--texto", p["texto"]],
                               stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            finally:
                FLAG.unlink(missing_ok=True)
            time.sleep(0.4)
            SO.matar(ov.pid)
    finally:
        FLAG.unlink(missing_ok=True)
        PID.unlink(missing_ok=True)

if __name__ == "__main__":
    main()
