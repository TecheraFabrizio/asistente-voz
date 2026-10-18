# Panel "Asistente personal", siempre arriba.
# Cabecera propia, borde cian, una caja con lo que vas dictando,
# y un spinner con lo que Claude esta haciendo.
# Solo lee archivos, no toca nada. Uso: python voz/panel.py

import tkinter as tk
from pathlib import Path

C = Path(__file__).parent
ESTADO = C / "estado.txt"      # escuchando / grabando / transcribiendo / dictando
DICTADO = C / "dictado.txt"    # lo que vas diciendo entre "va" y "listo"
ACCION = C / "accion.txt"      # que esta haciendo Claude ahora; vacio = nada

# colores
# paleta suave: nada de neon, colores apagados que no cansan
FONDO = "#12171f"
PANEL = "#1a2028"
BORDE = "#4a6a7a"
TEXTO = "#cfd6dc"
TENUE = "#55656f"
ACENTO = "#7fb3c4"

COLOR = {"escuchando": "#7cb88a", "grabando": "#c97b7b", "transcribiendo": "#c9a86b",
         "cargando": "#c9a86b", "dictando": "#7fb3c4"}
# como se muestra cada estado: en espera no dice "escuchando",
# "escuchando" es solo despues de la palabra clave. textos segun idioma (config.json)
import sys as _s; _s.path.insert(0, str(C))
import config as CFG
ETIQUETA = {"escuchando": CFG.t("espera"), "dictando": CFG.t("escuchando"),
            "grabando": CFG.t("grabando"), "transcribiendo": CFG.t("transcribiendo"), "cargando": CFG.t("cargando")}
ULTIMA = C / "ultima_respuesta.txt"   # ultima respuesta, para "ver respuesta"

SPIN = "◜◠◝◞◡◟"

def leer(p):
    try:
        return p.read_text(encoding="utf-8").strip()
    except Exception:
        return ""

root = tk.Tk()
root.overrideredirect(True)          # sin barra de windows
root.attributes("-topmost", True)
root.configure(bg=BORDE)             # el fondo de root hace de borde
root.geometry("540x320")
root.update_idletasks()
sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
root.geometry(f"+{sw-560}+{sh-400}")   # abajo a la derecha

cuerpo = tk.Frame(root, bg=FONDO)
cuerpo.pack(fill="both", expand=True, padx=1, pady=1)

# cabecera: titulo + boton cerrar, arrastrable
cab = tk.Frame(cuerpo, bg=PANEL, height=34)
cab.pack(fill="x")
cab.pack_propagate(False)
l_titulo = tk.Label(cab, text="◆  " + CFG.t("titulo"), fg=ACENTO, bg=PANEL,
                    font=("Consolas", 11, "bold"))
l_titulo.pack(side="left", padx=12)
cerrar = tk.Label(cab, text="✕", fg=TENUE, bg=PANEL, font=("Consolas", 12))
cerrar.pack(side="right", padx=12)
# toggle de idioma ES | EN: click cambia config.json; escucha y voz lo toman solos
l_lang = tk.Label(cab, text="", fg=ACENTO, bg=PANEL, font=("Consolas", 10, "bold"), cursor="hand2")
l_lang.pack(side="right", padx=8)
def _pintar_lang():
    l = CFG.lang()
    l_lang.configure(text="ES | en" if l == "es" else "es | EN")
def _toggle_lang(e=None):
    CFG.set_lang("en" if CFG.lang() == "es" else "es")
    _aplicar_lang()
_lang_vista = [CFG.lang()]
def _aplicar_lang():
    # textos de la interfaz en el idioma configurado. lo llama el toggle,
    # y tambien refrescar() si config.json cambio desde afuera (python voz/config.py en)
    _lang_vista[0] = CFG.lang()
    _pintar_lang()
    global ETIQUETA
    ETIQUETA = {"escuchando": CFG.t("espera"), "dictando": CFG.t("escuchando"),
                "grabando": CFG.t("grabando"), "transcribiendo": CFG.t("transcribiendo"), "cargando": CFG.t("cargando")}
    l_titulo.configure(text="◆  " + CFG.t("titulo"))
    if modal.get("win") is not None and modal.get("titulo"):
        modal["titulo"].configure(text="◆  " + CFG.t("respuesta"))   # el modal ya abierto tambien cambia
l_lang.bind("<Button-1>", _toggle_lang)
_pintar_lang()

# modelo y effort, a la derecha, leidos de settings.json de claude
l_modelo = tk.Label(cab, text="", fg=TENUE, bg=PANEL, font=("Consolas", 10))
l_modelo.pack(side="right", padx=8)

SETTINGS = Path.home() / ".claude" / "settings.json"
def modelo_effort():
    try:
        import json
        d = json.loads(SETTINGS.read_text(encoding="utf-8"))
        m = d.get("model", "?").split("[")[0]
        e = d.get("modelSettings", {}).get(m, {}).get("effortLevel") or d.get("effortLevel", "?")
        return f"{m.replace('claude-', '')}  ·  effort {e}"
    except Exception:
        return "modelo ?"
cerrar.bind("<Button-1>", lambda e: root.destroy())
cerrar.bind("<Enter>", lambda e: cerrar.configure(fg="#ff3b5c"))
cerrar.bind("<Leave>", lambda e: cerrar.configure(fg=TENUE))

_drag = {"x": 0, "y": 0}
def _ini(e): _drag["x"], _drag["y"] = e.x, e.y
def _mov(e): root.geometry(f"+{e.x_root - _drag['x']}+{e.y_root - _drag['y']}")
for wdg in (cab, cab.winfo_children()[0]):
    wdg.bind("<Button-1>", _ini)
    wdg.bind("<B1-Motion>", _mov)

# linea fina bajo la cabecera
tk.Frame(cuerpo, bg=BORDE, height=1).pack(fill="x")

# fila de estado del mic
fila = tk.Frame(cuerpo, bg=FONDO); fila.pack(fill="x", padx=14, pady=(10, 2))
punto = tk.Label(fila, text="●", fg=TENUE, bg=FONDO, font=("Consolas", 14)); punto.pack(side="left")
l_estado = tk.Label(fila, text="...", fg=TEXTO, bg=FONDO, font=("Consolas", 11)); l_estado.pack(side="left", padx=8)

# globo de dialogo del personaje: burbuja.txt tiene el texto; vacio = escondido. se borra solo a los 20 s
BURBUJA = C / "burbuja.txt"
l_burbuja = tk.Label(cuerpo, text="", fg=TEXTO, bg="#2a3442", font=("Segoe UI", 10), wraplength=300,
                     justify="left", padx=10, pady=5, highlightthickness=1, highlightbackground=ACENTO)
_burbuja = {"texto": "", "desde": 0.0}
def _refrescar_burbuja():
    import time as _t
    txt = leer(BURBUJA).strip()
    if txt != _burbuja["texto"]:
        _burbuja["texto"], _burbuja["desde"] = txt, _t.time()
    if txt and _t.time() - _burbuja["desde"] > 20:
        try: BURBUJA.write_text("", encoding="utf-8")
        except Exception: pass
        txt = ""
    if txt:
        l_burbuja.configure(text=txt)
        # pegado arriba del personaje, a la derecha de la fila de estado
        l_burbuja.place(in_=fila, relx=1.0, x=0, y=-2, anchor="ne")
        l_burbuja.lift()
    else:
        l_burbuja.place_forget()

# pasos de claude: una linea por paso, los hechos con ✓, el actual con spinner
# accion.txt tiene un paso por linea; vacio = no esta haciendo nada
# a la derecha, el personaje animado (Rover o Merlin) que trabaja cuando yo trabajo
# la fila tiene altura fija y el personaje un hueco fijo de 96x96: nada se mueve al cambiar de personaje ni al aparecer pasos
fila_pasos = tk.Frame(cuerpo, bg=FONDO, height=96); fila_pasos.pack(fill="x", padx=14, pady=(0, 6))
fila_pasos.pack_propagate(False)
hueco = tk.Frame(fila_pasos, bg=FONDO, width=96, height=96); hueco.pack(side="right")
hueco.pack_propagate(False)
l_accion = tk.Label(fila_pasos, text="", fg=ACENTO, bg=FONDO, font=("Consolas", 11),
                    justify="left", anchor="nw")
l_accion.pack(side="left", fill="both", expand=True)
agente = None
def _crear_agente(nombre):
    # arma el personaje centrado en su hueco; click derecho sobre el llama a esto con el siguiente
    global agente
    try:
        from agente import Agente
        if agente is not None:
            agente.destruir()
        agente = Agente(hueco, nombre, bg=FONDO, al_cambiar=_cambiar_agente)
        agente.place(relx=0.5, rely=0.5, anchor="center")
    except Exception:
        agente = None
def _cambiar_agente(nombre):
    CFG.set_agente(nombre)
    _crear_agente(nombre)
_crear_agente(CFG.agente())

# la caja unica con el dictado
marco = tk.Frame(cuerpo, bg=TENUE)
marco.pack(fill="both", expand=True, padx=14, pady=(0, 14))
t = tk.Text(marco, bg=PANEL, fg=TEXTO, font=("Segoe UI", 14), wrap="word",
            relief="flat", padx=10, pady=8,
            insertbackground=TEXTO, highlightthickness=0)
t.pack(fill="both", expand=True, padx=1, pady=1)

# la caja se puede corregir a mano: click, escribis, y lo que queda es lo que se manda
ENVIAR_AHORA = C / "dictado_enviar"
def _editado(e=None):
    if t.focus_get() is t:
        try:
            DICTADO.write_text(t.get("1.0", "end-1c").strip(), encoding="utf-8")
        except Exception:
            pass
def _enter(e):
    _editado()
    try:
        ENVIAR_AHORA.write_text("1", encoding="utf-8")
    except Exception:
        pass
    root.focus_set()
    return "break"          # que no meta un salto de linea
t.bind("<Button-1>", lambda e: t.focus_set())
t.bind("<KeyRelease>", _editado)
t.bind("<Return>", _enter)
t.bind("<Escape>", lambda e: root.focus_set())

tick = 0

# ---- modal de respuesta ----
# aparece cuando respuesta.txt tiene texto; se cierra con click o diciendo "cerralo"
RESP = C / "respuesta.txt"
modal = {"win": None, "txt": None}

def cerrar_modal():
    try:
        RESP.write_text("", encoding="utf-8")
    except Exception:
        pass
    if modal["win"] is not None:
        modal["win"].destroy()
        modal["win"] = None
        modal["txt"] = None

def rect_vscode():
    # donde esta la ventana de VS Code; el modal se abre en ese monitor. solo Windows
    if not _s.platform.startswith("win"):
        return None
    import ctypes, ctypes.wintypes as wt
    u = ctypes.windll.user32
    hallado = []
    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def cb(h, _):
        if u.IsWindowVisible(h):
            n = u.GetWindowTextLengthW(h)
            if n:
                b = ctypes.create_unicode_buffer(n + 1); u.GetWindowTextW(h, b, n + 1)
                if "Visual Studio Code" in b.value:
                    r = wt.RECT(); u.GetWindowRect(h, ctypes.byref(r))
                    if r.right - r.left > 400:
                        hallado.append((r.left, r.top, r.right, r.bottom))
                        return False
        return True
    u.EnumWindows(cb, 0)
    return hallado[0] if hallado else None

def formatear(mt, txt):
    # markdown simple: "# titulo", "- item", **negrita**. nada mas.
    import re as _re
    mt.configure(state="normal"); mt.delete("1.0", "end")
    for linea in txt.splitlines():
        if linea.startswith("# "):
            mt.insert("end", linea[2:] + "\n", "h"); continue
        if linea.startswith(("- ", "• ")):
            mt.insert("end", "   •  ", "b"); linea = linea[2:]
        pos = 0
        for m in _re.finditer(r"\*\*(.+?)\*\*", linea):
            mt.insert("end", linea[pos:m.start()]); mt.insert("end", m.group(1), "b"); pos = m.end()
        mt.insert("end", linea[pos:] + "\n")
    mt.configure(state="disabled")

class BarraScroll(tk.Canvas):
    # barrita de scroll fina, dibujada a mano. se esconde sola si no hay que scrollear.
    def __init__(self, padre, texto, **kw):
        super().__init__(padre, width=6, bg=FONDO, highlightthickness=0, **kw)
        self.texto = texto
        self.visible = False
        self.bind("<B1-Motion>", self._arrastre)
        self.bind("<Button-1>", self._arrastre)
        # cuando el canvas recien aparece mide 1 px; al tomar tamaño real, redibujo
        self.bind("<Configure>", lambda e: self.actualizar(*self.texto.yview()))

    def actualizar(self, a, b):
        a, b = float(a), float(b)
        if a <= 0.0 and b >= 1.0:
            if self.visible:
                self.pack_forget(); self.visible = False
            return
        if not self.visible:
            self.pack(side="right", fill="y", padx=(0, 4), pady=10); self.visible = True
        self.delete("all")
        h = self.winfo_height() or 1
        y0, y1 = int(a * h), max(int(b * h), int(a * h) + 24)
        self.create_rectangle(1, y0, 5, y1, fill=TENUE, outline="", width=0)

    def _arrastre(self, e):
        h = self.winfo_height() or 1
        a, b = self.texto.yview()
        self.texto.yview_moveto(max(0.0, e.y / h - (b - a) / 2))

def abrir_modal(txt):
    if modal["win"] is None:
        w = tk.Toplevel(root)
        w.overrideredirect(True)
        w.attributes("-topmost", True)
        w.attributes("-alpha", 0.93)            # un poco de transparencia
        w.configure(bg=BORDE)
        # pegado arriba del panel, mismo ancho
        root.update_idletasks()
        ancho = root.winfo_width()
        alto = 420
        x0, y0 = root.winfo_x(), root.winfo_y() - alto - 8
        w.geometry(f"{ancho}x{alto}+{x0}+{max(y0, 0)}")
        cu = tk.Frame(w, bg=FONDO); cu.pack(fill="both", expand=True, padx=1, pady=1)
        cb = tk.Frame(cu, bg=PANEL, height=34); cb.pack(fill="x"); cb.pack_propagate(False)
        tit = tk.Label(cb, text="◆  " + CFG.t("respuesta"), fg=ACENTO, bg=PANEL, font=("Consolas", 11, "bold")); tit.pack(side="left", padx=12)
        modal["titulo"] = tit          # para que el toggle de idioma lo cambie en vivo
        x = tk.Label(cb, text="✕", fg=TENUE, bg=PANEL, font=("Consolas", 12), cursor="hand2"); x.pack(side="right", padx=12)
        x.bind("<Button-1>", lambda e: cerrar_modal())
        x.bind("<Enter>", lambda e: x.configure(fg="#c97b7b"))
        x.bind("<Leave>", lambda e: x.configure(fg=TENUE))
        col = tk.Label(cb, text="▾", fg=TENUE, bg=PANEL, font=("Consolas", 13), cursor="hand2"); col.pack(side="right", padx=6)
        cuerpo_m = tk.Frame(cu, bg=FONDO); cuerpo_m.pack(fill="both", expand=True)
        tk.Frame(cuerpo_m, bg=BORDE, height=1).pack(fill="x")
        marco_t = tk.Frame(cuerpo_m, bg=FONDO); marco_t.pack(fill="both", expand=True)
        mt = tk.Text(marco_t, bg=FONDO, fg=TEXTO, font=("Segoe UI", 12), wrap="word",
                     relief="flat", padx=16, pady=12, state="disabled", highlightthickness=0,
                     spacing1=2, spacing3=6)
        barra = BarraScroll(marco_t, mt)
        mt.configure(yscrollcommand=barra.actualizar)
        mt.pack(side="left", fill="both", expand=True)
        mt.tag_configure("h", font=("Segoe UI", 14, "bold"), foreground=ACENTO, spacing3=8)
        mt.tag_configure("b", font=("Segoe UI", 12, "bold"))
        # colapsar: queda solo la cabecera, pegada al panel
        est = {"abierto": True}
        def colapsar(e=None):
            est["abierto"] = not est["abierto"]
            if est["abierto"]:
                cuerpo_m.pack(fill="both", expand=True)
                w.geometry(f"{ancho}x{alto}+{root.winfo_x()}+{max(root.winfo_y() - alto - 8, 0)}"); col.configure(text="▾")
            else:
                cuerpo_m.pack_forget()
                w.geometry(f"{ancho}x36+{root.winfo_x()}+{root.winfo_y() - 36 - 8}"); col.configure(text="▸")
        col.bind("<Button-1>", colapsar)
        modal["win"], modal["txt"], modal["ultimo"], modal["barra"] = w, mt, None, barra
    if modal.get("ultimo") != txt:
        formatear(modal["txt"], txt); modal["ultimo"] = txt
        modal["txt"].after(50, lambda: modal["barra"].actualizar(*modal["txt"].yview()))

def poner(txt):
    if t.focus_get() is t:            # estas escribiendo: no te piso el texto
        return
    if t.get("1.0", "end-1c") == txt:
        return
    t.delete("1.0", "end")
    t.insert("1.0", txt)
    t.see("end")

OCULTO = C / "oculto"       # lo crea el escucha con "assistant hide"; lo borra con "assistant show"
_visible = [True]
def _ver(mostrar):
    if mostrar == _visible[0]:
        return
    _visible[0] = mostrar
    for win in (root, modal.get("win")):
        if win is None: continue
        if mostrar: win.deiconify(); win.attributes("-topmost", True)
        else: win.withdraw()

def refrescar():
    global tick
    tick += 1
    if tick % 25 == 1:                    # cada 3 s alcanza
        l_modelo.configure(text=modelo_effort())
    if tick % 8 == 0 and CFG.lang() != _lang_vista[0]:   # cambiaron el idioma desde afuera
        _aplicar_lang()
    e = leer(ESTADO) or "apagado"
    l_estado.configure(text=ETIQUETA.get(e, e.upper()))
    punto.configure(fg=COLOR.get(e, TENUE))
    pasos = [p for p in leer(ACCION).splitlines() if p.strip()][-4:]
    if pasos:
        lineas = ["✓ " + p for p in pasos[:-1]] + [SPIN[tick % len(SPIN)] + " " + pasos[-1]]
        l_accion.configure(text="\n".join(lineas))
        if agente: agente.modo("trabajando")
    else:
        l_accion.configure(text="")
        if agente and agente._modo == "trabajando": agente.modo("listo")
    poner(leer(DICTADO))
    _ver(not OCULTO.exists())
    _refrescar_burbuja()
    r = leer(RESP)
    if r:
        abrir_modal(r)
    elif modal["win"] is not None:
        modal["win"].destroy(); modal["win"] = None; modal["txt"] = None
    root.after(120, refrescar)

refrescar()
root.mainloop()
