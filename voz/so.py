# Lo que cambia segun el sistema operativo: Windows, Linux o Mac.
# Todo lo demas del asistente es igual en los tres.
# Aca viven: el beep, lanzar y matar procesos, reproducir mp3, la voz sin internet y las librerias de CUDA.

import sys, os, shutil, subprocess, signal

WIN = sys.platform.startswith("win")
MAC = sys.platform == "darwin"
LINUX = not WIN and not MAC

_NADA = dict(stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def unica_instancia(nombre, carpeta):
    # si ya habia una copia corriendo (restart a medias, doble click), la mata: dos paneles encimados confunden
    pidf = os.path.join(carpeta, f"_{nombre}.pid")
    try:
        viejo = int(open(pidf).read().strip())
        if viejo != os.getpid():
            matar(viejo)
    except Exception:
        pass
    try:
        open(pidf, "w").write(str(os.getpid()))
    except Exception:
        pass

def cargar_cuda():
    # las librerias de CUDA vienen por pip (paquetes nvidia-*). hay que avisarle al sistema donde estan
    # en mac no hay CUDA: whisper corre en CPU
    if MAC:
        return
    import glob, site
    dirs = []
    for b in site.getsitepackages() + [site.getusersitepackages()]:
        dirs += glob.glob(os.path.join(b, "nvidia", "*", "bin" if WIN else "lib"))
    if WIN:
        os.environ["PATH"] = os.pathsep.join(dirs) + os.pathsep + os.environ["PATH"]
        return
    # linux: el PATH no alcanza. se cargan las .so a mano antes de importar whisper
    # dos pasadas porque algunas dependen de otras y el orden importa
    import ctypes
    sos = [s for d in dirs for s in sorted(glob.glob(os.path.join(d, "*.so*")))]
    for _ in range(2):
        for s in sos:
            try:
                ctypes.CDLL(s, mode=ctypes.RTLD_GLOBAL)
            except OSError:
                pass

def beep(ok=True):
    # un pitido corto: agudo = bien, grave = no
    if WIN:
        import winsound
        winsound.Beep(880 if ok else 440, 90)
        return
    try:
        import numpy as np, sounddevice as sd
        fs = 44100
        t = np.arange(int(fs * 0.09)) / fs
        onda = (0.2 * np.sin(2 * np.pi * (880 if ok else 440) * t)).astype("float32")
        sd.play(onda, fs)
    except Exception:
        print("\a", end="", flush=True)

def pythonw():
    # interprete sin ventana de consola. en linux y mac el normal ya no abre ventana
    if WIN:
        return sys.executable.replace("python.exe", "pythonw.exe")
    return sys.executable

def lanzar(cmd):
    # proceso aparte, sin ventana, que despues se puede matar junto con sus hijos
    kw = dict(_NADA)
    if WIN:
        kw["creationflags"] = subprocess.CREATE_NO_WINDOW
    else:
        kw["start_new_session"] = True     # grupo propio: matar() lo baja entero
    return subprocess.Popen(cmd, **kw)

def matar(pid):
    # mata el proceso y todos sus hijos (el reproductor de audio, por ejemplo)
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return
    try:
        if WIN:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], **_NADA)
        else:
            try:
                os.killpg(os.getpgid(pid), signal.SIGKILL)
            except ProcessLookupError:
                os.kill(pid, signal.SIGKILL)
    except Exception:
        pass

def matar_por_nombre(fragmento):
    # mata todo proceso cuya linea de comando contenga ese texto (ej: "overlay.py")
    try:
        if WIN:
            ps = ("Get-CimInstance Win32_Process | ? { $_.CommandLine -like '*" + fragmento + "*' } "
                  "| % { Stop-Process -Id $_.ProcessId -Force }")
            subprocess.run(["powershell", "-NoProfile", "-Command", ps], **_NADA)
        else:
            subprocess.run(["pkill", "-f", fragmento], **_NADA)
    except Exception:
        pass

def _reproductor(mp3):
    # primer reproductor de mp3 que haya instalado
    if MAC and shutil.which("afplay"):
        return ["afplay", mp3]
    for c in (["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", mp3],
              ["mpv", "--no-video", "--really-quiet", mp3],
              ["mpg123", "-q", mp3],
              ["cvlc", "--play-and-exit", "-q", mp3]):
        if shutil.which(c[0]):
            return c
    return None

def reproducir(mp3):
    # toca un mp3 y espera a que termine
    mp3 = str(mp3)
    if WIN and shutil.which("ffplay"):
        # ffplay arranca en 0.3 s; el MediaPlayer de .NET via PowerShell tarda 2 s en arrancar (medido 17-oct)
        subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", mp3], creationflags=subprocess.CREATE_NO_WINDOW, **_NADA)
        return
    if WIN:
        # MediaPlayer de .NET, sin ventana
        ps = (
            "Add-Type -AssemblyName presentationCore; "
            "$p = New-Object System.Windows.Media.MediaPlayer; "
            f"$p.Open([Uri]'{mp3}'); "
            "$t0 = Get-Date; while (-not $p.NaturalDuration.HasTimeSpan) { Start-Sleep -Milliseconds 30; "
            "if (((Get-Date) - $t0).TotalSeconds -gt 5) { break } }; "
            "$p.Play(); "
            "$d = $p.NaturalDuration.TimeSpan.TotalMilliseconds; Start-Sleep -Milliseconds ([int]$d + 150); $p.Close()"
        )
        subprocess.run(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps], **_NADA)
        return
    cmd = _reproductor(mp3)
    if cmd is None:
        raise RuntimeError("no hay reproductor de mp3: instala ffmpeg (ffplay) o mpv")
    subprocess.run(cmd, **_NADA)

def voz_local(texto):
    # voz del sistema, sin internet. suena peor pero suena
    try:
        if WIN:
            ps = ("Add-Type -AssemblyName System.Speech; "
                  "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Speak(" + repr(texto) + ")")
            subprocess.run(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps], **_NADA)
        elif MAC and shutil.which("say"):
            subprocess.run(["say", texto], **_NADA)
        elif shutil.which("spd-say"):
            subprocess.run(["spd-say", "-w", texto], **_NADA)
        elif shutil.which("espeak-ng"):
            subprocess.run(["espeak-ng", texto], **_NADA)
        elif shutil.which("espeak"):
            subprocess.run(["espeak", texto], **_NADA)
    except Exception:
        pass
