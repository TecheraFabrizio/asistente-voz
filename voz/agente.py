# Personaje animado para el panel (Rover, el perrito de la busqueda de Windows XP, o Merlin el mago).
# Sprites y datos de animacion del proyecto clippy.js (MIT). Van en voz/_agentes/<Nombre>/map.png + agent.json.
# Uso en tkinter:
#   ag = Agente(padre, "Rover"); ag.pack(); ag.modo("trabajando")  /  ag.modo("quieto")

import json, random, tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk

C = Path(__file__).parent / "_agentes"

# que animaciones usa cada modo
MODOS = {
    "Rover": {
        "trabajando": ["Searching", "Thinking", "Writing", "ImageSearching", "Books", "GetAttention"],
        "quieto": ["Idle", "RestPose", "LookUp", "Pleased"],
        "listo": ["Congratulate", "CharacterSucceeds", "Pleased"],
    },
    "Merlin": {
        "trabajando": ["Processing", "Searching", "Writing", "Thinking", "Reading", "DoMagic1"],
        "quieto": ["Idle1_1", "Idle1_2", "RestPose", "Blink", "LookLeft", "LookRight"],
        "listo": ["Congratulate", "Pleased", "DoMagic2"],
    },
}

class Agente(tk.Canvas):
    def __init__(self, padre, nombre="Rover", escala=1.0, bg="#12171f", **kw):
        self.nombre = nombre
        carpeta = C / nombre
        self.datos = json.loads((carpeta / "agent.json").read_text(encoding="utf-8"))
        self.fw, self.fh = self.datos["framesize"]
        self.escala = escala
        self.w, self.h = int(self.fw * escala), int(self.fh * escala)
        super().__init__(padre, width=self.w, height=self.h, bg=bg, highlightthickness=0, **kw)
        self.mapa = Image.open(carpeta / "map.png").convert("RGBA")
        self.cache = {}
        self._modo = "quieto"
        self._anim = None
        self._i = 0
        self._job = None
        self._item = self.create_image(0, 0, anchor="nw")
        self._siguiente_anim()

    def _cuadro(self, imagenes):
        # un frame puede apilar varias capas (overlays); se dibujan en orden
        clave = tuple(map(tuple, imagenes))
        if clave not in self.cache:
            base = Image.new("RGBA", (self.fw, self.fh), (0, 0, 0, 0))
            for x, y in imagenes:
                capa = self.mapa.crop((x, y, x + self.fw, y + self.fh))
                base.alpha_composite(capa)
            if self.escala != 1.0:
                base = base.resize((self.w, self.h), Image.LANCZOS)
            self.cache[clave] = ImageTk.PhotoImage(base)
        return self.cache[clave]

    def modo(self, m):
        if m != self._modo:
            self._modo = m
            self._siguiente_anim()

    def _siguiente_anim(self):
        if self._job:
            self.after_cancel(self._job); self._job = None
        opciones = MODOS.get(self.nombre, {}).get(self._modo) or ["Idle"]
        opciones = [o for o in opciones if o in self.datos["animations"]] or list(self.datos["animations"])[:1]
        self._anim = self.datos["animations"][random.choice(opciones)]["frames"]
        self._i = 0
        self._paso()

    def _paso(self):
        if self._i >= len(self._anim):
            # termino la animacion: elijo otra del mismo modo (si era "listo", vuelvo a quieto)
            if self._modo == "listo":
                self._modo = "quieto"
            self._siguiente_anim(); return
        f = self._anim[self._i]
        if f.get("images"):
            self.itemconfigure(self._item, image=self._cuadro(f["images"]))
        self._i += 1
        self._job = self.after(max(int(f.get("duration", 100)), 30), self._paso)
