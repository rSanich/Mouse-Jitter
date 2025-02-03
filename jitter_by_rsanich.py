import tkinter as tk
from tkinter import ttk
import ctypes
import threading
import time

# WinAPI Structures
class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", ctypes.c_void_p),
        ("message", ctypes.c_uint),
        ("wParam", ctypes.c_ulong),
        ("lParam", ctypes.c_long),
        ("time", ctypes.c_ulong),
        ("pt", ctypes.c_long * 2)
    ]

# WinAPI Constants and Functions
user32 = ctypes.windll.user32
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WH_MOUSE_LL = 14

class MouseInput(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("mi", MouseInput)]

class JitterConfig:
    def __init__(self):
        self.horizontal = 15
        self.vertical = 15
        self.speed = 0.001
        self.active = False
        self.running = True
        self.left_pressed = False
        self.right_pressed = False

config = JitterConfig()

def move_mouse(dx, dy):
    inp = Input()
    inp.type = 0
    inp.mi.dx = dx
    inp.mi.dy = dy
    inp.mi.mouseData = 0
    inp.mi.dwFlags = 0x0001
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

def jitter_loop():
    while config.running:
        if config.active:
            move_mouse(config.horizontal, config.vertical)
            time.sleep(config.speed)
            move_mouse(-config.horizontal, -config.vertical)
            time.sleep(config.speed)
        else:
            time.sleep(0.01)

HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_int, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong))

@HOOKPROC
def mouse_hook(nCode, wParam, lParam):
    if wParam == WM_LBUTTONDOWN:
        config.left_pressed = True
    elif wParam == WM_LBUTTONUP:
        config.left_pressed = False
    elif wParam == WM_RBUTTONDOWN:
        config.right_pressed = True
    elif wParam == WM_RBUTTONUP:
        config.right_pressed = False
    
    config.active = config.left_pressed and config.right_pressed
    return user32.CallNextHookEx(None, nCode, wParam, lParam)

def start_hook():
    hook = user32.SetWindowsHookExW(WH_MOUSE_LL, mouse_hook, None, 0)
    msg = MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0: pass

class JitterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mouse Jitter by rSanich")
        self.geometry("450x350")
        
        self.create_widgets()
        self.setup_validation()
        self.setup_threads()
        
    def create_widgets(self):
        # Horizontal Jitter
        self.h_frame = ttk.Frame(self)
        self.h_label = ttk.Label(self.h_frame, text="Horizontal (1-25): ")
        self.h_scale = ttk.Scale(self.h_frame, from_=1, to=25, value=15, length=200)
        self.h_entry = ttk.Entry(self.h_frame, width=7)
        self.h_entry.insert(0, "15")
        
        # Vertical Jitter
        self.v_frame = ttk.Frame(self)
        self.v_label = ttk.Label(self.v_frame, text="Vertical (1-25):       ")
        self.v_scale = ttk.Scale(self.v_frame, from_=1, to=25, value=15, length=200)
        self.v_entry = ttk.Entry(self.v_frame, width=7)
        self.v_entry.insert(0, "15")
        
        # Speed
        self.s_frame = ttk.Frame(self)
        self.s_label = ttk.Label(self.s_frame, text="Speed (0.0001-0.1):")
        self.s_scale = ttk.Scale(self.s_frame, from_=0.001, to=0.1, value=0.001, length=200)
        self.s_entry = ttk.Entry(self.s_frame, width=7)
        self.s_entry.insert(0, "0.001")
        
        # Apply button
        self.apply_btn = ttk.Button(self, text="Apply", command=self.update_settings)
        
        # Information message
        self.note_label = ttk.Label(self, text="The default settings are recommended.")
        
        # Arrangement of elements
        self.h_label.pack(side=tk.LEFT, padx=5)
        self.h_scale.pack(side=tk.LEFT, expand=True)
        self.h_entry.pack(side=tk.LEFT, padx=5)
        self.h_frame.pack(pady=5, fill=tk.X)
        
        self.v_label.pack(side=tk.LEFT, padx=5)
        self.v_scale.pack(side=tk.LEFT, expand=True)
        self.v_entry.pack(side=tk.LEFT, padx=5)
        self.v_frame.pack(pady=5, fill=tk.X)
        
        self.s_label.pack(side=tk.LEFT, padx=5)
        self.s_scale.pack(side=tk.LEFT, expand=True)
        self.s_entry.pack(side=tk.LEFT, padx=5)
        self.s_frame.pack(pady=5, fill=tk.X)
        
        self.apply_btn.pack(pady=15)
        self.note_label.pack(pady=10)
        
    def setup_validation(self):
        self.h_scale.configure(command=lambda v: self.h_entry.delete(0, tk.END) or self.h_entry.insert(0, f"{float(v):.0f}"))
        self.v_scale.configure(command=lambda v: self.v_entry.delete(0, tk.END) or self.v_entry.insert(0, f"{float(v):.0f}"))
        self.s_scale.configure(command=lambda v: self.s_entry.delete(0, tk.END) or self.s_entry.insert(0, f"{float(v):.3f}"))
        
        self.h_entry.bind("<FocusOut>", self.validate_horizontal)
        self.v_entry.bind("<FocusOut>", self.validate_vertical)
        self.s_entry.bind("<FocusOut>", self.validate_speed)
        
    def validate_horizontal(self, event):
        try:
            val = min(25, max(1, int(self.h_entry.get())))
            self.h_entry.delete(0, tk.END)
            self.h_entry.insert(0, str(val))
            self.h_scale.set(val)
        except:
            self.h_entry.delete(0, tk.END)
            self.h_entry.insert(0, str(config.horizontal))
            
    def validate_vertical(self, event):
        try:
            val = min(25, max(1, int(self.v_entry.get())))
            self.v_entry.delete(0, tk.END)
            self.v_entry.insert(0, str(val))
            self.v_scale.set(val)
        except:
            self.v_entry.delete(0, tk.END)
            self.v_entry.insert(0, str(config.vertical))
            
    def validate_speed(self, event):
        try:
            val = min(0.1, max(0.001, float(self.s_entry.get())))
            self.s_entry.delete(0, tk.END)
            self.s_entry.insert(0, f"{val:.3f}")
            self.s_scale.set(val)
        except:
            self.s_entry.delete(0, tk.END)
            self.s_entry.insert(0, f"{config.speed:.3f}")
        
    def setup_threads(self):
        self.hook_thread = threading.Thread(target=start_hook, daemon=True)
        self.jitter_thread = threading.Thread(target=jitter_loop, daemon=True)
        self.hook_thread.start()
        self.jitter_thread.start()
        
    def update_settings(self):
        try:
            config.horizontal = int(self.h_entry.get())
            config.vertical = int(self.v_entry.get())
            config.speed = float(self.s_entry.get())
        except:
            pass
        
    def on_closing(self):
        config.running = False
        self.destroy()

if __name__ == "__main__":
    app = JitterApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()