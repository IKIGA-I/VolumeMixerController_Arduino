import serial
import threading
import time
import tkinter as tk
from tkinter import ttk
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume, ISimpleAudioVolume
from PIL import Image, ImageTk

SERIAL_PORT = 'COM7'
BAUD_RATE = 9600
APP_LIST = ["System", "Spotify", "VLC"]
LOGO_FILES = ["system.png", "spotify.png", "vlc.png"]

class VolumeController:
    def __init__(self):
        self.devices = AudioUtilities.GetSpeakers()
        self.interface = self.devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(self.interface, POINTER(IAudioEndpointVolume))

    def set_system_volume(self, value):
        self.volume.SetMasterVolumeLevelScalar(value / 100.0, None)

    def set_app_volume(self, app_index, value):
        sessions = AudioUtilities.GetAllSessions()
        app_name = APP_LIST[app_index]
        for session in sessions:
            if session.Process and app_name.lower() in session.Process.name().lower():
                volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                volume.SetMasterVolume(value / 100.0, None)

    def get_system_volume(self):
        return int(self.volume.GetMasterVolumeLevelScalar() * 100)

    def get_app_volume(self, app_index):
        sessions = AudioUtilities.GetAllSessions()
        app_name = APP_LIST[app_index]
        for session in sessions:
            if session.Process and app_name.lower() in session.Process.name().lower():
                volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                return int(volume.GetMasterVolume() * 100)
        return None  # Return None if app session not found
                

class VolumeApp(tk.Tk):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.current_app_index = 0
        self.configure(bg="#2C2F33")
        self.overrideredirect(True)
        self.geometry_center(420, 440)

        self.load_logos()
        self.setup_styles()
        self.create_title_bar()
        self.create_main_widgets()

        self.serial_port = tk.StringVar(value=SERIAL_PORT)

        port_frame = tk.Frame(self, bg="#2C2F33")
        port_frame.pack(pady=(5, 0))

        tk.Label(port_frame, text="COM Port:", fg="white", bg="#2C2F33", font=("Segoe UI", 10)).pack(side=tk.LEFT)
        self.port_entry = tk.Entry(port_frame, textvariable=self.serial_port, width=10)
        self.port_entry.pack(side=tk.LEFT, padx=(5, 0))
        tk.Button(port_frame, text="Connect", command=self.connect_serial, bg="#7289DA", fg="white", bd=0).pack(side=tk.LEFT, padx=10)
        tk.Frame(self, height=10, bg="#2C2F33").pack()  # Spacer after port selection

    def geometry_center(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TScale",
            troughcolor="#40444B",
            background="#7289DA",
            sliderthickness=20,
            thickness=10,
            bordercolor="#2C2F33",
            lightcolor="#7289DA",
            darkcolor="#7289DA"
        )

    def load_logos(self):
        self.logos = []
        for file in LOGO_FILES:
            try:
                img = Image.open(file).convert("RGBA").resize((64, 64), Image.Resampling.LANCZOS)
                self.logos.append(ImageTk.PhotoImage(img))
            except:
                self.logos.append(None)

    def create_title_bar(self):
        self.title_bar = tk.Frame(self, bg="#23272A", height=30)
        self.title_bar.pack(fill=tk.X, side=tk.TOP)
        self.title_bar.bind("<Button-1>", self.start_move)
        self.title_bar.bind("<B1-Motion>", self.do_move)

        tk.Label(self.title_bar, text="🔊 Volume Controller", fg="white", bg="#23272A", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=10)
        tk.Button(self.title_bar, text="✕", command=self.destroy, bg="#23272A", fg="white", bd=0).pack(side=tk.RIGHT, padx=10)

    def start_move(self, event):
        self._x, self._y = event.x, event.y

    def do_move(self, event):
        x = self.winfo_x() + event.x - self._x
        y = self.winfo_y() + event.y - self._y
        self.geometry(f"+{x}+{y}")

    def create_main_widgets(self):
        app_frame = tk.Frame(self, bg="#2C2F33")
        app_frame.pack(pady=10, padx=20, fill="x")

        container = tk.Frame(self, bg="#2C2F33")
        container.pack(fill='x')   # make container full width
        # Frame to center the logo buttons
        logo_button_frame = tk.Frame(self, bg="#2C2F33")
        logo_button_frame.pack(pady=10, anchor="center")


        # App logo buttons
        self.logo_buttons = []
        for i, (logo, name) in enumerate(zip(self.logos, APP_LIST)):
            if logo:
                btn = tk.Button(app_frame, image=logo, command=lambda idx=i: self.set_app_index(idx), bg="#2C2F33", relief="flat", bd=0)
            else:
                btn = tk.Button(app_frame, text=name, command=lambda idx=i: self.set_app_index(idx), bg="#2C2F33", fg="white", font=("Segoe UI", 10, "bold"))

            btn.pack(side=tk.LEFT, padx=30)
            self.logo_buttons.append(btn)


        self.app_label = tk.Label(self, text=APP_LIST[self.current_app_index], fg="white", bg="#2C2F33", font=("Segoe UI", 16, "bold"))
        self.app_label.pack(pady=5)

        vol_frame = tk.Frame(self, bg="#2C2F33")
        vol_frame.pack(padx=20, fill="x")

        self.volume_slider = ttk.Scale(vol_frame, from_=0, to=100, orient="horizontal", command=self.update_volume, style="TScale")
        self.volume_slider.set(50)
        self.volume_slider.pack(fill="x")

        self.volume_label = tk.Label(self, text="50%", font=("Segoe UI", 20), fg="white", bg="#2C2F33")
        self.volume_label.pack(pady=10)

        self.log_box = tk.Text(self, height=6, state="disabled", bg="#23272A", fg="white", font=("Consolas", 10), relief="flat")
        self.log_box.pack(padx=20, fill="both", expand=True)

        self.spacer = tk.Frame(self, bg="#2C2F33", height=20)
        self.spacer.pack(fill=tk.X)

    def update_volume(self, val):
        val = int(float(val))
        self.volume_label.config(text=f"{val}%")
        if self.current_app_index == 0:
            self.controller.set_system_volume(val)
        else:
            self.controller.set_app_volume(self.current_app_index, val)

    def set_app_index(self, index):
        if 0 <= index < len(APP_LIST):
            self.current_app_index = index
            self.update_app_display()
            self.highlight_selected_button()
            self.log_message(f"Switched to: {APP_LIST[index]}")
            self.update_volume_slider()  # <- Add this line

    def update_volume_slider(self):
        if self.current_app_index == 0:
            current_volume = self.controller.get_system_volume()
        else:
            current_volume = self.controller.get_app_volume(self.current_app_index)
        
        if current_volume is not None:
            self.volume_slider.set(current_volume)
            self.volume_label.config(text=f"{current_volume}%")
        else:
            self.log_message(f"Could not fetch volume for {APP_LIST[self.current_app_index]}")

    def highlight_selected_button(self):
        for i, btn in enumerate(self.logo_buttons):
            if i == self.current_app_index:
                btn.config(bg="#7289DA", highlightthickness=2, highlightbackground="#99AAB5", highlightcolor="#99AAB5")
            else:
                btn.config(bg="#2C2F33", highlightthickness=0)

    def update_app_display(self):
        self.app_label.config(text=APP_LIST[self.current_app_index])

    def log_message(self, msg):
        self.log_box.config(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def connect_serial(self):
        port = self.serial_port.get()
        self.log_message(f"Connecting to {port}...")
        self.serial_thread = threading.Thread(target=lambda: self.read_serial_dynamic(port), daemon=True)
        self.serial_thread.start()

    def read_serial_dynamic(self, port):
        try:
            with serial.Serial(port, BAUD_RATE, timeout=1) as ser:
                while True:
                    line = ser.readline().decode("utf-8").strip()
                    if line:
                        print("Received:", line)
                        self.after(0, lambda l=line: self.log_message(f"> {l}"))

                        if line.startswith("APP:"):
                            index = int(line.split(":")[1])
                            self.after(0, lambda idx=index: self.set_app_index(idx))

                        elif line.startswith("VOLUME:"):
                            _, idx_str, val_str = line.split(":")
                            index = int(idx_str)
                            val = int(val_str)
                            self.after(0, lambda: self.volume_slider.set(val))
                            if index == 0:
                                self.controller.set_system_volume(val)
                            else:
                                self.controller.set_app_volume(index, val)
        except serial.SerialException as e:
            self.after(0, lambda: self.log_message(f"Serial error: {e}"))


    
if __name__ == "__main__":
    vc = VolumeController()
    app = VolumeApp(vc)
    app.mainloop()
