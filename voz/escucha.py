# Escucha el mic todo el tiempo.
# Cuando decis "va", lo que sigue va a entrada.txt.
# Claude Code vigila ese archivo y procesa.
#
# Uso:  python voz/escucha.py            (mic por defecto)
#       python voz/escucha.py --mic 2    (elegir mic por numero)
#       python voz/escucha.py --listar   (ver mics)

import sys, time, queue, re, os

# lo que depende del sistema operativo (beep, procesos, audio, CUDA) esta en so.py
import so as SO
SO.unica_instancia("escucha", os.path.dirname(os.path.abspath(__file__)))   # mata un escucha anterior si quedo vivo
SO.cargar_cuda()      # antes de importar whisper: le dice donde estan las librerias de la GPU

import numpy as np
import sounddevice as sd
from pathlib import Path
from faster_whisper import WhisperModel
# detector de voz (Silero, viene con faster-whisper): distingue habla de ruido en 1 a 6 ms.
# medido 17-oct: silencio y ruido blanco -> no; voz, incluso 20 veces mas baja -> si
from faster_whisper.vad import VadOptions, get_speech_timestamps
VAD = VadOptions(threshold=0.3, min_speech_duration_ms=50, min_silence_duration_ms=100)

CARPETA = Path(__file__).parent
SALIDA = CARPETA / "entrada.txt"
LOG = CARPETA / "todo.txt"          # todo lo que escucho, para debug
ESTADO = CARPETA / "estado.txt"     # lo lee el panel
DICTADO = CARPETA / "dictado.txt"   # texto que vas dictando, lo muestra el panel

FS = 16000                           # whisper quiere 16 kHz
BLOQUE = 0.05                        # 50 ms por bloque
UMBRAL = 0.012                       # volumen minimo para "esta hablando"
SILENCIO_FIN = 0.5                   # segundos callado = termino la frase
MAX_FRASE = 15                       # corte duro en segundos
MAX_DICTADO = 120                    # si no decis "listo" en 2 min, manda lo que hay

import config as CFG
LANG = CFG.lang()                    # "es" o "en"; se cambia con --lang o python voz/config.py en

# los comandos se aceptan en los dos idiomas siempre. el idioma solo cambia
# lo que whisper espera, la voz que habla y los textos del panel.
# palabras que cuentan como "va" / "go" (whisper a veces lo escribe distinto)
WAKE = re.compile(r"^\W*(va|ba|bah|vah|vaa|wa|van|bar|bam|bye|bai|vai|fa|pa|pam|vam|baby|bang|ya"
                  r"|go|goal|gold|ghost|joe)\b[\s,.:!¡]*", re.I)
# "listo" / "done" cierra el dictado y manda todo junto
FIN = re.compile(r"[\s,.:!¡]*\b(listo|lito|listos|liston|visto|done|dun|ready|send it|that's it)\W*$", re.I)
# "cancela" / "cancel" tira el dictado
CANCEL = re.compile(r"^\W*(cancel[aá]|cancelar|olvidalo|olv[ií]dalo|cancel|never mind|nevermind|forget it)\W*$", re.I)
# "cerralo" cierra el modal de respuesta
# "ok" y "dale" ya no cierran: son muletillas y cerraban el modal sin querer
CERRAR = re.compile(r"^\W*(cerralo|cerrarlo|cerr[aá]|cerrar|cierra|cierralo|ci[eé]rralo|close|dismiss)"
                    r"(\s+(el|la|ese|esa|eso|esto|it|the|that|this)?\s*(modal|ventana|respuesta|cartel|window|answer|response|popup)?)?\W*$", re.I)
RESPUESTA = CARPETA / "respuesta.txt"
ULTIMA = CARPETA / "ultima_respuesta.txt"   # la guarda el panel; "ver respuesta" la vuelve a abrir
# "ver respuesta" reabre el modal con la ultima respuesta
VER = re.compile(r"^\W*(ver|mostr\w*|abr\w*|abre|show|open|display)\w*\b.{0,25}\b(respuesta|modal|model|modelo|ventana|answer|response|window|popup)\b.{0,15}$", re.I)
# "narralo" lee en voz alta la explicacion de lo ultimo que señale (narracion.txt)
NARRAR = re.compile(r"^\W*(narr[aá]lo|narr[aá]melo|narralo|d[aá]ramelo|n[aá]rramelo|narramelo|arr[aá]melo|\w{0,2}arr[aá]melo"
                    r"|\w{0,3}\s?r+[aá]\s?m[ei]\s?lo"      # "a rami lo", "arrámelo", "dárame lo": como sea que whisper lo escriba
                    r"|explic[aá]lo|explic[aá]melo|l[eé]+lo|l[eé]+melo|cont[aá]melo|contalo"
                    r"|le[eé](me)?( el texto| la respuesta| el modal)?( en voz alta)?|(read|breathe|reed) ?(the text|it|the answer)? ?(aloud|out loud)( the answer| the text)?|narrat(e|es|ed|ing)( it)?( to me)?|narration|read (it|that|this|the (text|answer|modal|panel|response))( to me| in the (modal|panel))?|read me the (text|answer)|explain( it)?|tell me)\W*$", re.I)
# "callate" / "shut up" corta la narracion
CALLAR = re.compile(r"^\W*(call[aá]te|c[aá]llate|par[aá]|basta|silencio|stop|shut up|quiet|be quiet|silence)\W*$", re.I)
NARRACION = CARPETA / "narracion.txt"
# siglas y simbolos como se dicen, no como se escriben
AL_OIDO = [
    (r"\bP/E fwd\b", "forward price earnings"), (r"\bP/E\b", "price earnings"), (r"\bPEG\b", "peg"),
    (r"\bfwd\b", "forward"), (r"\bP/L\b", "profit and loss"), (r"\bB/S\b", "buy sell"),
    (r"\bMKT\b", "market"), (r"\bQty\b", "quantity"), (r"\bTIF\b", "time in force"),
    (r"\bYTD\b", "year to date"), (r"\bETF(s)?\b", r"E T F\1"),
    (r"\$\s?([\d.,]+)", r"\1 dólares"), (r"(\d)\s?%", r"\1 por ciento"), (r"\bn/d\b", "sin dato"),
    (r"\s[·|]\s", ", "), (r"\s—\s", ", "),
]
HABLAR = CARPETA / "hablar.txt"        # si claude escribe algo aca, se dice en voz alta y se borra
# "borrá las flechas / el dibujo" cierra los overlays directo
# "assistant hide" / "assistant show" (o "asistente ocultar" / "asistente mostrar") esconden y traen el panel
# "hi, the assistant" y "high the assistant" son "hide the assistant" mal oido
OCULTAR = re.compile(r"^\W*((assistant|asistente)\W+(hide|hi|high|ocult\w*)|(hide|hi|high|ocult\w*)\W+(the\s+|el\s+)?(assistant|asistente))\W*$", re.I)
MOSTRAR = re.compile(r"^\W*((assistant|asistente)\W+(show|mostr\w*)|(show|mostr\w*)\W+(the\s+|el\s+)?(assistant|asistente))\W*$", re.I)
OCULTO = CARPETA / "oculto"             # si existe, el panel se esconde
BORRAR = re.compile(r"^\W*(borr\w*|sac\w*|quit\w*|cerr\w*|vora|clear|remove|delete|erase|hide)\b.{0,25}\b(flecha\w*|dibujo\w*|marca\w*|gr[aá]fico\w*|cartel\w*|arrow\w*|drawing\w*|mark\w*|overlay\w*)\b.{0,10}$", re.I)

def borrar_overlays():
    SO.matar_por_nombre("overlay.py")
# "va" al final de la frase: "quiero que abras. va"
WAKE_FIN = re.compile(r"[\s,.:!¡]*\b(va|ba|bam|bye)\W*$", re.I)
# frases que whisper inventa con audio corto; nunca las dijiste
INVENTOS = ("suscríbete", "suscribete", "hasta la próxima", "hasta la proxima", "hola",
            "gracias", "adiós", "adios", "chau", "amara.org", "subtítulos", "subtitulos",
            "thank you", "thanks for watching", "subscribe", "see you", "bye bye")
CORTO = 0.8                          # segundos de voz; menos que esto es una palabra suelta
# whisper a veces copia la frase de ejemplo del prompt y la pega al final. se borra siempre
ECO_PROMPT = re.compile(r"[\s,.]*\b(abr[ií] la p[aá]gina|open the page)\b\W*", re.I)
ENVIAR_AHORA = CARPETA / "dictado_enviar"   # el panel lo crea cuando apretas Enter en la caja

def es_invento(t):
    t = t.lower()
    return any(i in t for i in INVENTOS)

def listar():
    for i, d in enumerate(sd.query_devices()):
        if d["max_input_channels"] > 0:
            print(i, d["name"])

def estado(txt):
    ESTADO.write_text(txt, encoding="utf-8")

def beep(ok=True):
    SO.beep(ok)

def enviar(hora, orden):
    # una orden que es solo un invento de whisper ("¡Suscríbete!") no se manda
    if len(orden.split()) <= 3 and es_invento(orden):
        print(f"  (ignorado, invento: {orden})")
        beep(False)
        return
    with SALIDA.open("a", encoding="utf-8") as f:
        f.write(f"{hora} | {orden}\n")
    print(f"  -> enviado: {orden}")
    # el panel muestra que la orden entro; el hook de claude sigue desde ahi
    (CARPETA / "accion.txt").write_text(CFG.t("procesando") + "\n", encoding="utf-8")
    # marca que hay una orden de voz en curso: al terminar, claude avisa hablando
    (CARPETA / "orden_pendiente").write_text("1", encoding="utf-8")
    beep(True)

import subprocess
_voz = {"p": None, "cola": []}
FLAG_HABLANDO = CARPETA / "_hablando"    # la pone tour.py mientras narra
TOUR_PID = CARPETA / "_tour.pid"

def voz_activa():
    # True mientras hablar.py o un tour siguen hablando
    p = _voz["p"]
    return (p is not None and p.poll() is None) or FLAG_HABLANDO.exists()

BURBUJA = CARPETA / "burbuja.txt"      # globo del personaje: muestra lo que digo en voz alta
def decir(texto):
    # lo que se dice tambien aparece en el globo del personaje (la primera frase, corta)
    try:
        frase = re.split(r"(?<=[.!?])\s+", texto.strip())[0][:120]
        BURBUJA.write_text(frase, encoding="utf-8")
    except Exception:
        pass
    # si ya hay voz sonando, va a la cola: nada se pisa
    if voz_activa():
        _voz["cola"].append(texto)
        return
    (CARPETA / "_decir.txt").write_text(texto, encoding="utf-8")
    _voz["p"] = SO.lanzar([sys.executable, str(CARPETA / "hablar.py"), str(CARPETA / "_decir.txt")])

def atender_cola():
    if _voz["cola"] and not voz_activa():
        decir(_voz["cola"].pop(0))

def callar():
    # corta todo: lo que suena, la cola, y el tour si hay
    _voz["cola"].clear()
    p = _voz["p"]
    if p is not None and p.poll() is None:
        SO.matar(p.pid)      # tambien al hijo que reproduce el audio
    _voz["p"] = None
    if TOUR_PID.exists():
        try:
            SO.matar(TOUR_PID.read_text().strip())
        except Exception:
            pass
        TOUR_PID.unlink(missing_ok=True)
        # el overlay del paso queda huerfano: lo mato por nombre de archivo
        SO.matar_por_nombre("_paso.json")
    FLAG_HABLANDO.unlink(missing_ok=True)

def narrar():
    # lee en voz alta lo ultimo que dejo claude.
    # si hay una version hablada (narracion.txt) mas nueva que el modal, va esa.
    # si no, lee el modal limpiando formato y traduciendo siglas al oido.
    txt = ""
    cand = [a for a in (NARRACION, RESPUESTA, ULTIMA) if a.exists() and a.read_text(encoding="utf-8").strip()]
    if cand:
        cand.sort(key=lambda a: a.stat().st_mtime, reverse=True)
        # narracion gana si es tan nueva como el modal (menos de 2 min de diferencia)
        if NARRACION in cand and (cand[0] == NARRACION or NARRACION.stat().st_mtime >= cand[0].stat().st_mtime - 120):
            txt = NARRACION.read_text(encoding="utf-8")
        else:
            txt = cand[0].read_text(encoding="utf-8")
    txt = re.sub(r"\*\*(.+?)\*\*", r"\1", txt)
    txt = re.sub(r"^#+\s*", "", txt, flags=re.M)
    txt = re.sub(r"^\s*[-•]\s*", "", txt, flags=re.M)
    for a, b in AL_OIDO:
        txt = re.sub(a, b, txt)
    decir(txt.strip() or CFG.t("nada_narrar"))

def main():
    args = sys.argv[1:]
    if "--listar" in args:
        listar(); return
    mic = None
    if "--mic" in args:
        mic = int(args[args.index("--mic") + 1])
    global LANG
    if "--lang" in args:
        LANG = args[args.index("--lang") + 1]
        CFG.set_lang(LANG)
    print("idioma / language:", LANG)

    estado("cargando")
    print("cargando whisper...")
    # small: 0.7 s por frase. medium: 2.7 s. turbo: 9.9 s (medido 17-oct-2026, RTX 4060 Ti).
    # small con beam 5 es el mejor equilibrio entre rapidez y precision.
    try:
        modelo = WhisperModel("small", device="cuda", compute_type="float16")
    except Exception as ex:
        # sin GPU NVIDIA (o sin sus librerias): CPU. anda, tarda 2 a 4 s por frase
        print("sin GPU, uso CPU:", type(ex).__name__)
        modelo = WhisperModel("small", device="cpu", compute_type="int8")
    # calentar: la primera llamada es lenta
    modelo.transcribe(np.zeros(FS, dtype=np.float32), language=LANG)
    print("listo. deci 'va' y la orden.")
    estado("escuchando")

    q = queue.Queue()
    def cb(indata, frames, t, status):
        q.put(indata[:, 0].copy())

    dictado = None          # None = no estoy dictando; lista = frases acumuladas
    dictado_desde = 0

    with sd.InputStream(samplerate=FS, channels=1, dtype="float32",
                        blocksize=int(FS * BLOQUE), device=mic, callback=cb):
        buf = []
        hablando = False
        callado = 0.0
        while True:
            x = q.get()
            # apretaste Enter en la caja del panel: manda lo que hay escrito
            if ENVIAR_AHORA.exists():
                # tambien sin "va": escribiste en la caja y apretaste Enter
                try: ENVIAR_AHORA.unlink()
                except Exception: pass
                orden = DICTADO.read_text(encoding="utf-8").strip() if DICTADO.exists() else ""
                dictado = None
                buf = []; hablando = False; callado = 0.0
                if orden:
                    enviar(time.strftime("%H:%M:%S"), orden)
                    DICTADO.write_text("", encoding="utf-8")
                else:
                    beep(False)
                estado("escuchando")
                continue
            atender_cola()
            # si claude dejo algo para decir, lo digo
            try:
                if HABLAR.stat().st_size > 0:
                    t = HABLAR.read_text(encoding="utf-8")
                    HABLAR.write_text("", encoding="utf-8")
                    decir(t)
            except FileNotFoundError:
                pass
            vol = float(np.sqrt(np.mean(x ** 2)))
            if vol > UMBRAL:
                if not hablando:
                    hablando = True
                    buf = []
                    estado("grabando")
                buf.append(x)
                callado = 0.0
            elif hablando:
                buf.append(x)
                callado += BLOQUE
                if callado >= SILENCIO_FIN or len(buf) * BLOQUE > MAX_FRASE:
                    hablando = False
                    audio = np.concatenate(buf)
                    if len(audio) < FS * 0.3:      # menos de 0.3 s: ruido
                        estado("escuchando")
                        continue
                    estado("transcribiendo")
                    LANG = CFG.lang()          # por si tocaron el toggle del panel
                    t0 = time.time()
                    dur_voz = len(audio) / FS - SILENCIO_FIN
                    corto = dur_voz < CORTO
                    if dur_voz < 0.15:
                        continue            # un golpe, un click: no es una palabra. "done" dura 0.3 s (medido)
                    rms = float(np.sqrt(np.mean(audio ** 2)))
                    # el detector de voz rechazo clips reales (uno de 0.5 s a volumen 0.083, 17-oct 23:45), asi que
                    # solo ayuda: un clip pasa si tiene volumen (ruido medido: 0.004-0.006) o si el detector dice que es voz
                    es_voz = rms >= 0.0065 or bool(get_speech_timestamps(audio, VAD))
                    if not es_voz:
                        print(f"[no es voz {dur_voz:.1f}s rms={rms:.3f}]")
                        continue            # hubo sonido pero no es una voz: no se transcribe ni pita
                    if corto:
                        # relleno con silencio: whisper inventa menos con clips cortos
                        pad = np.zeros(int(FS * 0.4), dtype=np.float32)
                        audio = np.concatenate([pad, audio, pad])
                    # clip corto ("va", "listo"): idioma fijo, que no adivine con una palabra.
                    # frase larga: whisper detecta solo si hablaste en español o en ingles y lo escribe en ese idioma
                    if corto:
                        # con prompt: sin el, "go" sale como "You" u "Okay" (medido 17-oct 22:16).
                        # el ruido que sale como "go." se frena con el minimo de 0.3 s y el volumen
                        idioma, prompt = LANG, CFG.t("prompt_whisper")
                    else:
                        idioma, prompt = None, "va. listo. go. done."
                    segs, info = modelo.transcribe(audio, language=idioma, beam_size=5,
                                                   vad_filter=False, condition_on_previous_text=False,
                                                   initial_prompt=prompt)
                    texto = " ".join(s.text for s in segs).strip()
                    if not corto and info.language not in ("es", "en"):
                        # detecto otra cosa (ruido, musica): vuelvo al idioma configurado
                        segs, info = modelo.transcribe(audio, language=LANG, beam_size=5,
                                                       vad_filter=False, condition_on_previous_text=False,
                                                       initial_prompt=CFG.t("prompt_whisper"))
                        texto = " ".join(s.text for s in segs).strip()
                    texto = ECO_PROMPT.sub(" ", texto).strip()   # saca el eco del prompt
                    dt = time.time() - t0
                    if not texto:
                        estado("escuchando")
                        continue
                    hora = time.strftime("%H:%M:%S")
                    with LOG.open("a", encoding="utf-8") as f:
                        f.write(f"{hora} | {texto}\n")
                    print(f"[{dt:.2f}s {info.language} {dur_voz:.1f}s rms={rms:.3f}] {texto}")

                    ahora = time.time()
                    m = WAKE.match(texto)
                    mf = WAKE_FIN.search(texto)
                    pocas = len(texto.split()) <= 2
                    if voz_activa():
                        # mientras hablo solo acepto "callate" o "va"; lo demas es mi propia voz
                        if CALLAR.match(texto):
                            callar()
                            estado("escuchando")
                            continue
                        if (corto and pocas and (m or mf)) or NARRAR.match(texto):
                            # dijo "va" o "narrámelo" encima de la voz: la corto y sigo con el comando
                            callar()
                        else:
                            estado("escuchando")
                            continue

                    if dictado is None and NARRAR.match(texto):
                        narrar()
                        estado("escuchando")
                        continue

                    if dictado is None and OCULTAR.match(texto):
                        OCULTO.write_text("1", encoding="utf-8"); beep(True)
                        estado("escuchando")
                        continue
                    if dictado is None and MOSTRAR.match(texto):
                        OCULTO.unlink(missing_ok=True); beep(True)
                        estado("escuchando")
                        continue

                    if dictado is None and BORRAR.match(texto):
                        borrar_overlays()
                        beep(True)
                        estado("escuchando")
                        continue

                    if dictado is None and CERRAR.match(texto):
                        # cierra el modal de respuesta
                        RESPUESTA.write_text("", encoding="utf-8")
                        estado("escuchando")
                        continue

                    if dictado is None and VER.match(texto):
                        # reabre el modal con la ultima respuesta
                        if ULTIMA.exists():
                            RESPUESTA.write_text(ULTIMA.read_text(encoding="utf-8"), encoding="utf-8")
                        estado("escuchando")
                        continue

                    if dictado is None:
                        # arranca si: empieza con va, o termina con va,
                        # o es un clip corto de 1-2 palabras (whisper inventa cualquier cosa con "va")
                        if m:
                            texto = texto[m.end():].strip()
                        elif mf:
                            texto = texto[:mf.start()].strip()
                        else:
                            # un "listo" suelto o cualquier otra cosa sin "va": no es para mi
                            estado("escuchando")
                            continue
                        dictado = []
                        dictado_desde = ahora
                        DICTADO.write_text("", encoding="utf-8")   # borra lo viejo de la caja
                        BURBUJA.write_text("", encoding="utf-8")   # y el globo del personaje
                        beep(True)

                    if CANCEL.match(texto):
                        dictado = None
                        beep(False)
                        estado("escuchando")
                        continue

                    # "assistant hide" / "show" tambien en medio del dictado; no se agregan al texto
                    if OCULTAR.match(texto):
                        OCULTO.write_text("1", encoding="utf-8"); beep(True); estado("dictando"); continue
                    if MOSTRAR.match(texto):
                        OCULTO.unlink(missing_ok=True); beep(True); estado("dictando"); continue

                    # "quiet" / "callate" en medio del dictado: corta la voz, no se agrega al texto
                    if CALLAR.match(texto):
                        callar()
                        estado("dictando")
                        continue

                    # "va" de nuevo mientras dictas: borra lo anterior y arranca de cero
                    # (vale tambien si lo dijiste lento: un clip largo que solo contiene "go")
                    solo_va = pocas and m is not None and not texto[m.end():].strip()
                    if dictado is not None and ((corto and pocas and (m or mf)) or solo_va):
                        dictado = []
                        dictado_desde = ahora
                        DICTADO.write_text("", encoding="utf-8")
                        beep(True)
                        estado("dictando")
                        continue

                    fin = FIN.search(texto)
                    if fin:
                        texto = texto[:fin.start()].strip()
                    elif corto and pocas and es_invento(texto):
                        # clip corto con un invento tipico: era "listo"
                        fin = True
                        texto = ""
                    # lo que hay en la caja manda: si lo corregiste a mano, se respeta
                    try:
                        caja = DICTADO.read_text(encoding="utf-8").strip()
                    except Exception:
                        caja = " ".join(dictado).strip()
                    if caja != " ".join(dictado).strip():
                        dictado = [caja] if caja else []
                    if texto and not (corto and es_invento(texto)):
                        dictado.append(texto)

                    DICTADO.write_text(" ".join(dictado), encoding="utf-8")
                    if fin or ahora - dictado_desde > MAX_DICTADO:
                        orden = " ".join(dictado).strip()
                        dictado = None
                        if orden and NARRAR.match(orden):
                            # "va, narramelo, listo": es un pedido de narrar, no una orden para claude
                            narrar()
                        elif orden:
                            enviar(hora, orden)
                        else:
                            beep(False)
                        estado("escuchando")
                    else:
                        estado("dictando")

if __name__ == "__main__":
    main()
