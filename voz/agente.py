# Personaje animado para el panel: Rover (perrito de la busqueda de Windows XP), Merlin (mago) o Clippy.
# Sprites y datos de animacion del proyecto clippy.js (MIT). Van en voz/_agentes/<Nombre>/map.png + agent.json.
#
# Uso en tkinter:
#   ag = Agente(padre, "Rover", al_cambiar=funcion); ag.pack()
#   ag.modo("trabajando") / ag.modo("quieto") / ag.modo("listo")
# Click izquierdo: hace una interaccion. Click derecho: pasa al siguiente personaje (llama al_cambiar).

import json, random, tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk

C = Path(__file__).parent / "_agentes"
ORDEN = ["Rover", "Merlin", "Clippy"]        # orden al cambiar con click derecho
ESCALA = {"Rover": 1.0, "Merlin": 0.7, "Clippy": 0.75}

# que animaciones usa cada modo, por personaje
MODOS = {
    "Rover": {
        "trabajando": ["Searching", "Thinking", "Writing", "ImageSearching", "Books", "GetAttention"],
        "quieto": ["Idle", "RestPose", "LookUp", "LookUpLeft"],
        "listo": ["Congratulate", "CharacterSucceeds", "Pleased"],
        "click": ["ClickedOn", "Sports", "Cooking", "Travel", "Money", "Shopping", "Celebrity", "Surprised",
                  "Embarrassed", "Acknowledge", "Greet", "GestureLeft"],
    },
    "Merlin": {
        "trabajando": ["Processing", "Searching", "Writing", "Thinking", "Reading", "DoMagic1", "Read"],
        "quieto": ["Idle1_1", "Idle1_2", "Idle1_3", "Idle2_1", "RestPose", "Blink", "LookLeft", "LookRight"],
        "listo": ["Congratulate", "Pleased", "DoMagic2", "Congratulate_2"],
        "click": ["Wave", "DoMagic1", "DoMagic2", "GestureUp", "Surprised", "Confused", "Explain", "Announce",
                  "Greet", "Alert", "Suggest", "Sad"],
    },
    "Clippy": {
        "trabajando": ["Searching", "Thinking", "Writing", "Processing", "CheckingSomething", "GetTechy", "Print"],
        "quieto": ["Idle1_1", "IdleAtom", "IdleEyeBrowRaise", "IdleFingerTap", "IdleHeadScratch", "IdleRopePile",
                   "IdleSideToSide", "IdleSnooze", "RestPose", "LookLeft", "LookRight"],
        "listo": ["Congratulate", "Wave", "GetArtsy"],
        "click": ["Wave", "Greeting", "Alert", "Explain", "GetArtsy", "GetWizardy", "EmptyTrash", "SendMail",
                  "Save", "GestureUp", "GestureDown", "GoodBye"],
    },
}

# animacion segun lo que claude esta haciendo (lo dice el hook en tipo.txt)
TRABAJO = {
    "leer":     {"Rover": ["Books"], "Merlin": ["Reading", "Read"], "Clippy": ["CheckingSomething"]},
    "escribir": {"Rover": ["Writing"], "Merlin": ["Writing"], "Clippy": ["Writing"]},
    "buscar":   {"Rover": ["Searching"], "Merlin": ["Searching"], "Clippy": ["Searching"]},
    "web":      {"Rover": ["ImageSearching", "Searching"], "Merlin": ["Searching"], "Clippy": ["Searching", "GetTechy"]},
    "comando":  {"Rover": ["Thinking", "GetAttention"], "Merlin": ["Processing", "DoMagic1"], "Clippy": ["Processing", "GetTechy"]},
    "pensar":   {"Rover": ["Thinking"], "Merlin": ["Thinking"], "Clippy": ["Thinking"]},
    "chrome":   {"Rover": ["ImageSearching"], "Merlin": ["Searching"], "Clippy": ["GetTechy"]},
}

def siguiente(nombre):
    i = ORDEN.index(nombre) if nombre in ORDEN else -1
    return ORDEN[(i + 1) % len(ORDEN)]

class Agente(tk.Canvas):
    def __init__(self, padre, nombre="Rover", escala=None, bg="#12171f", al_cambiar=None, **kw):
        self.nombre = nombre
        carpeta = C / nombre
        self.datos = json.loads((carpeta / "agent.json").read_text(encoding="utf-8"))
        self.fw, self.fh = self.datos["framesize"]
        self.escala = escala if escala is not None else ESCALA.get(nombre, 1.0)
        # sobre el color clave de una ventana transparente, los bordes semitransparentes del sprite
        # se mezclan con ese color y queda un halo. con alfa duro (todo o nada) no hay halo
        self.alfa_duro = str(bg).lower() == "#ff00fe"
        self.w, self.h = int(self.fw * self.escala), int(self.fh * self.escala)
        super().__init__(padre, width=self.w, height=self.h, bg=bg, highlightthickness=0, cursor="hand2", **kw)
        self.mapa = Image.open(carpeta / "map.png").convert("RGBA")
        self.cache = {}
        self._modo = "quieto"
        self._tipo = ""              # clase de trabajo en curso (leer, escribir, ...)
        self._anim = None
        self._i = 0
        self._job = None
        self._item = self.create_image(0, 0, anchor="nw")
        self.bind("<Button-1>", lambda e: self.modo("click", forzar=True))
        if al_cambiar:
            self.bind("<Button-3>", lambda e: al_cambiar(siguiente(self.nombre)))
        self._siguiente_anim()

    def _cuadro(self, imagenes):
        # un frame puede apilar varias capas (overlays); se dibujan en orden
        clave = tuple(map(tuple, imagenes))
        if clave not in self.cache:
            base = Image.new("RGBA", (self.fw, self.fh), (0, 0, 0, 0))
            for x, y in imagenes:
                base.alpha_composite(self.mapa.crop((x, y, x + self.fw, y + self.fh)))
            if self.escala != 1.0:
                base = base.resize((self.w, self.h), Image.LANCZOS)
            if self.alfa_duro:
                base.putalpha(base.getchannel("A").point(lambda a: 255 if a >= 110 else 0))
            self.cache[clave] = ImageTk.PhotoImage(base)
        return self.cache[clave]

    def modo(self, m, forzar=False):
        if m != "trabajando":
            self._tipo = ""
        if m != self._modo or forzar:
            self._modo = m
            self._siguiente_anim()

    def trabajar(self, tipo):
        # trabajando en algo concreto: la animacion acompaña (lee, escribe, busca...)
        tipo = tipo if tipo in TRABAJO else ""
        if self._modo != "trabajando" or tipo != self._tipo:
            self._modo, self._tipo = "trabajando", tipo
            self._siguiente_anim()

    def _siguiente_anim(self):
        if self._job:
            self.after_cancel(self._job); self._job = None
        opciones = MODOS.get(self.nombre, {}).get(self._modo) or ["Idle"]
        if self._modo == "trabajando" and self._tipo:
            opciones = TRABAJO[self._tipo].get(self.nombre, opciones)
        opciones = [o for o in opciones if o in self.datos["animations"]] or list(self.datos["animations"])[:1]
        self._anim = self.datos["animations"][random.choice(opciones)]["frames"]
        self._i = 0
        self._paso()

    def _paso(self):
        if self._i >= len(self._anim):
            # termino: si era un gesto puntual (click / listo), vuelvo a quieto; si no, otra del mismo modo
            if self._modo in ("listo", "click"):
                self._modo = "quieto"
            self._siguiente_anim(); return
        f = self._anim[self._i]
        if f.get("images"):
            self.itemconfigure(self._item, image=self._cuadro(f["images"]))
        self._i += 1
        self._job = self.after(max(int(f.get("duration", 100)), 30), self._paso)

    def destruir(self):
        if self._job:
            self.after_cancel(self._job); self._job = None
        self.destroy()
