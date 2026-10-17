"""
overlay.py
Capa transparente sobre la pantalla para señalar cosas con flechas y texto.
Los clicks pasan a través: podés seguir usando la app de abajo.

Uso: python overlay.py anotaciones.json
Se cierra con el botón "✕ borrar dibujos" o matando el proceso.

JSON:
{
  "x": 1920, "y": 0, "w": 1920, "h": 1080,      # monitor a cubrir
  "items": [
    {"type": "box",   "x": 10, "y": 10, "w": 100, "h": 30},
    {"type": "arrow", "x1": 0, "y1": 0, "x2": 50, "y2": 50},
    {"type": "label", "x": 0, "y": 0, "text": "hola"},
    {"type": "num",   "x": 0, "y": 0, "n": 1}
  ]
}
"""
import sys, json, ctypes, tkinter as tk, tkinter.font as tkfont

# pixeles reales aunque Windows tenga escala 125%
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

KEY = "#ff00fe"     # este color se vuelve transparente
AMAR = "#ffc400"
FONDO = "#141414"
TEXTO = "#ffe078"

def click_through(win):
    # hace que los clicks atraviesen la ventana
    GWL_EXSTYLE, WS_EX_LAYERED, WS_EX_TRANSPARENT = -20, 0x80000, 0x20
    hwnd = ctypes.windll.user32.GetParent(win.winfo_id())
    st = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, st | WS_EX_LAYERED | WS_EX_TRANSPARENT)

def main():
    cfg = json.load(open(sys.argv[1], encoding="utf-8-sig"))
    X, Y, W, H = cfg.get("x", 0), cfg.get("y", 0), cfg.get("w", 1920), cfg.get("h", 1080)

    root = tk.Tk()
    root.overrideredirect(True)
    root.geometry(f"{W}x{H}+{X}+{Y}")
    root.attributes("-topmost", True)
    root.attributes("-transparentcolor", KEY)
    root.config(bg=KEY)
    c = tk.Canvas(root, bg=KEY, highlightthickness=0, width=W, height=H)
    c.pack(fill="both", expand=True)
    f = tkfont.Font(family="Segoe UI", size=13, weight="bold")
    fn = tkfont.Font(family="Segoe UI", size=14, weight="bold")

    for it in cfg.get("items", []):
        t = it["type"]
        if t == "box":
            c.create_rectangle(it["x"], it["y"], it["x"] + it["w"], it["y"] + it["h"], outline=AMAR, width=3)
        elif t == "arrow":
            c.create_line(it["x1"], it["y1"], it["x2"], it["y2"], fill=AMAR, width=3, arrow="last", arrowshape=(16, 20, 7))
        elif t == "label":
            tw = f.measure(it["text"]); th = f.metrics("linespace")
            c.create_rectangle(it["x"] - 8, it["y"] - 6, it["x"] + tw + 8, it["y"] + th + 6, fill=FONDO, outline=AMAR, width=2)
            c.create_text(it["x"], it["y"], text=it["text"], fill=TEXTO, font=f, anchor="nw")
        elif t == "num":
            c.create_oval(it["x"], it["y"], it["x"] + 32, it["y"] + 32, fill=FONDO, outline=AMAR, width=3)
            c.create_text(it["x"] + 16, it["y"] + 16, text=str(it["n"]), fill=TEXTO, font=fn)

    root.update_idletasks()
    click_through(root)

    # botón aparte para cerrar (este sí recibe clicks)
    b = tk.Toplevel(root)
    b.overrideredirect(True)
    b.attributes("-topmost", True)
    b.geometry(f"+{X + W - 190}+{Y + H - 90}")
    tk.Button(b, text="✕ borrar dibujos", bg=FONDO, fg=TEXTO, activebackground="#333", activeforeground=TEXTO,
              font=f, relief="flat", padx=10, pady=4, command=root.destroy).pack()

    root.mainloop()

if __name__ == "__main__":
    main()
