# Dice un texto en voz alta, en español rioplatense (o inglés segun config.json).
# Voces neuronales de Microsoft por internet (edge-tts).
# Habla frase por frase: la primera arranca en menos de un segundo,
# las siguientes se generan mientras suena la anterior.
# Si no hay internet, cae a la voz de Windows (inglesa, suena mal pero suena).
#
# Uso:  python voz/hablar.py --texto "Listo"
#       python voz/hablar.py archivo.txt

import sys, re, asyncio, subprocess
from pathlib import Path

C = Path(__file__).parent
sys.path.insert(0, str(C))
import config as CFG
VOZ = CFG.t("voz")          # es-UY-MateoNeural o en-US-GuyNeural segun config.json
TMP = C / "_tts"            # mp3 de cada frase
TMP.mkdir(exist_ok=True)

def frases(texto):
    # corta por punto, signo de pregunta/exclamacion o salto de linea
    partes = re.split(r"(?<=[.!?¿¡:])\s+|\n+", texto)
    return [p.strip() for p in partes if p and p.strip()]

def reproducir(mp3):
    # MediaPlayer de .NET; espera a que termine
    ps = (
        "Add-Type -AssemblyName presentationCore; "
        "$p = New-Object System.Windows.Media.MediaPlayer; "
        f"$p.Open([Uri]'{mp3}'); "
        "$t0 = Get-Date; while (-not $p.NaturalDuration.HasTimeSpan) { Start-Sleep -Milliseconds 30; "
        "if (((Get-Date) - $t0).TotalSeconds -gt 5) { break } }; "
        "$p.Play(); "
        "$d = $p.NaturalDuration.TimeSpan.TotalMilliseconds; Start-Sleep -Milliseconds ([int]$d + 150); $p.Close()"
    )
    subprocess.run(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

async def generar(texto, destino):
    import edge_tts
    await edge_tts.Communicate(texto, VOZ, rate="+12%").save(str(destino))

async def hablar_async(texto):
    fs = frases(texto)
    if not fs:
        return
    # la primera frase se genera sola (1.2 s medido); las demas arrancan cuando la primera ya suena
    await generar(fs[0], TMP / "000.mp3")
    tareas = [asyncio.create_task(generar(f, TMP / f"{i:03d}.mp3")) for i, f in enumerate(fs) if i > 0]
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, reproducir, TMP / "000.mp3")
    for i, t in enumerate(tareas, start=1):
        await t
        await loop.run_in_executor(None, reproducir, TMP / f"{i:03d}.mp3")

def sapi(texto):
    ps = ("Add-Type -AssemblyName System.Speech; "
          "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Speak(" + repr(texto) + ")")
    subprocess.run(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def hablar(texto):
    texto = texto.strip()
    if not texto:
        return
    try:
        asyncio.run(hablar_async(texto))
    except Exception:
        sapi(texto)

if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--texto":
        hablar(" ".join(a[1:]))
    elif a:
        hablar(Path(a[0]).read_text(encoding="utf-8"))
