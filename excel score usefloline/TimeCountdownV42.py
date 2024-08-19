from tkinter import *
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import threading
import time
from PIL import Image


from tkinter import Canvas, NW, RAISED, SUNKEN, RIDGE, DISABLED, BOTH
from PIL import Image, ImageTk

class CountdownTimer:
    def __init__(self, root, channels, initial_width=800, initial_height=600):
        self.root = root
        self.channels = channels
        self.prev_width = initial_width  # Initialize prev_width
        self.prev_height = initial_height  # Initialize prev_height
        self.resize_timer = None
        self.resizing = False  # Flag to indicate whether resizing is in progress
        self.master_timer = {
            'minutes': tk.IntVar(value=0),
            'seconds': tk.IntVar(value=0),
            'milliseconds': tk.IntVar(value=0)
        }
        self.timers = []
        self.stopped_times = []  # Initialize list to track stopped times for ranking

        # Set the initial size of the window
        self.root.geometry(f"{initial_width}x{initial_height}")

        self.create_widgets()

        # Bind the <Configure> event to handle window resizing
        self.root.bind('<Configure>', self.on_resize)

    def create_widgets(self):
        self.root.style = ttk.Style()
        self.root.style.theme_use('clam')  # Use a cross-platform theme

        # Configure custom styles for buttons with adjusted padding
        self.root.style.configure('Stop.TButton', background='#FF0000', foreground='#FFFFFF', font=("Helvetica", 12, 'bold'), padding=0)
        self.root.style.configure('Reset.TButton', background='#FFD700', foreground='#000000', font=("Helvetica", 12, 'bold'), padding=0)
        self.root.style.map('Stop.TButton', background=[('active', '#CC0000')])  # Active color for STOP button
        self.root.style.map('Reset.TButton', background=[('active', '#FFC700')])  # Active color for RESET button
        self.root.style.configure('Set.TButton', background='#6666CC', foreground='#FFFFFF', font=("Helvetica", 12, 'bold'), padding=2)
        self.root.style.configure('Start.TButton', background='#5CD65C', foreground='#FFFFFF', font=("Helvetica", 12, 'bold'), padding=0)

        # Customize ttk Labels for a more consistent appearance
        self.root.style.configure('TLabel', background='#f0f0f0', foreground='#000000', font=("Helvetica", 12))

        # Create a canvas for background image
        self.canvas = Canvas(self.root)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # Load and place background image
        self.load_background_image()

        # Configure root window resizing
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Master timer frame
        self.create_master_timer_frame()

        # Create the main frame for the timers
        self.create_timers_frame()

        # Frame for ranking display
        self.create_ranking_frame()

        self.bind_keys()  # Bind the keys after creating all widgets

        # Configure fullscreen behavior
        self.root.attributes('-fullscreen', True)  # Set fullscreen mode
        self.root.bind('<Escape>', self.exit_fullscreen)  # Bind Esc key to exit fullscreen

    def load_background_image(self):
        self.bg_image = Image.open("ibotbg.jpg")
        self.bg_image = self.bg_image.resize((self.root.winfo_screenwidth(), self.root.winfo_screenheight()), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        self.bg_image_id = self.canvas.create_image(0, 0, anchor=NW, image=self.bg_photo)

    def create_master_timer_frame(self):
        self.master_frame = ttk.Frame(self.root, padding=10, relief=SUNKEN, style='TFrame')
        self.master_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=0)

        self.master_label = ttk.Label(self.master_frame, text="Master Timer:", font=("Helvetica", 14, 'bold'))
        self.master_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.master_min_label = ttk.Label(self.master_frame, text="Min:")
        self.master_min_label.grid(row=1, column=0, sticky="e")
        self.master_min_entry = ttk.Entry(self.master_frame, textvariable=self.master_timer['minutes'], width=2, font=("Helvetica", 12))
        self.master_min_entry.grid(row=1, column=1, sticky="w")

        self.master_sec_label = ttk.Label(self.master_frame, text="Sec:")
        self.master_sec_label.grid(row=1, column=2, sticky="e")
        self.master_sec_entry = ttk.Entry(self.master_frame, textvariable=self.master_timer['seconds'], width=2, font=("Helvetica", 12))
        self.master_sec_entry.grid(row=1, column=3, sticky="w")

        self.master_msec_label = ttk.Label(self.master_frame, text="mSec:")
        self.master_msec_label.grid(row=1, column=4, sticky="e")
        self.master_msec_entry = ttk.Entry(self.master_frame, textvariable=self.master_timer['milliseconds'], width=3, font=("Helvetica", 12))
        self.master_msec_entry.grid(row=1, column=5, sticky="w")

        self.set_all_button = ttk.Button(self.master_frame, text="Set All", command=self.set_all_timers, style='Set.TButton')
        self.set_all_button.grid(row=1, column=6, padx=5, sticky="w")
        self.start_all_button = ttk.Button(self.master_frame, text="Start All", command=self.start_all_timers, style='Start.TButton')
        self.start_all_button.grid(row=1, column=7, padx=5, sticky="w")
        self.reset_all_button = ttk.Button(self.master_frame, text="Reset All", command=self.reset_all_timers, style='Reset.TButton')
        self.reset_all_button.grid(row=1, column=8, padx=5, sticky="w")

    def create_timers_frame(self):
        self.timers_frame = ttk.Frame(self.root, padding=5, relief=RIDGE, style='TFrame')
        self.timers_frame.grid(row=2, column=0, sticky="nsew", padx=3, pady=3)

        rows = (self.channels + 4) // 5  # Ensure enough rows to fit all channels
        columns = 5

        for row in range(rows):
            self.timers_frame.grid_rowconfigure(row, weight=1, minsize=160)
        for col in range(columns):
            self.timers_frame.grid_columnconfigure(col, weight=1)

        for i in range(self.channels):
            frame = ttk.Frame(self.timers_frame, padding=10, relief=RAISED, style='TFrame')
            frame.grid(row=i // columns, column=i % columns, padx=5, pady=10, sticky="nsew")
            self.timers.append({
                'minutes': tk.IntVar(value=0),
                'seconds': tk.IntVar(value=0),
                'milliseconds': tk.IntVar(value=0),
                'running': False,
                'paused': False,
                'count_thread': None,
                'remaining_time': (i + 1) * 60,
                'start_button': None,
                'stop_button': None,
                'reset_button': None,
                'stopped_time': None,
                'stopped_time_label': None,
                'frame': frame  # Store a reference to the frame
            })

            self.create_timer_widgets(frame, i)

    def create_timer_widgets(self, frame, i):
        ttk.Label(frame, text=f"Team {i + 1}:", font=("Helvetica", 12, 'bold')).grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Minutes label and entry
        ttk.Label(frame, text="Min:").grid(row=1, column=0, sticky="w", padx=2, pady=5)
        ttk.Entry(frame, textvariable=self.timers[i]['minutes'], width=2, font=("Helvetica", 30)).grid(row=2, column=0, sticky="e", padx=2, pady=5)

        # Seconds label and entry
        ttk.Label(frame, text="Sec:").grid(row=1, column=1, sticky="w", padx=2, pady=5)
        ttk.Entry(frame, textvariable=self.timers[i]['seconds'], width=2, font=("Helvetica", 30)).grid(row=2, column=1, sticky="e", padx=2, pady=5)

        # Milliseconds label and entry
        ttk.Label(frame, text="mSec:").grid(row=1, column=2, sticky="w", padx=2, pady=5)
        ttk.Entry(frame, textvariable=self.timers[i]['milliseconds'], width=1, font=("Helvetica", 30)).grid(row=2, column=2, sticky="e", padx=2, pady=5)

        # Configure column weights to prevent expansion
        frame.grid_columnconfigure(0, weight=0)  # Team label column
        frame.grid_columnconfigure(1, weight=0)  # Minutes label column
        frame.grid_columnconfigure(2, weight=0)  # Seconds label column
        frame.grid_columnconfigure(3, weight=0)  # Milliseconds label column

        # Buttons (compact size)
        start_button = ttk.Button(frame, text="START", command=lambda idx=i: self.start_timer(idx), style='Start.TButton', width=6)
        start_button.grid(row=3, column=0, padx=0, pady=5, sticky="nsew")
        self.timers[i]['start_button'] = start_button

        stop_button = ttk.Button(frame, text="STOP", command=lambda idx=i: self.stop_timer(idx), style='Stop.TButton', state=DISABLED, width=6)
        stop_button.grid(row=3, column=1, padx=0, pady=5, sticky="nsew")
        self.timers[i]['stop_button'] = stop_button

        reset_button = ttk.Button(frame, text="RESET", command=lambda idx=i: self.reset_timer(idx), style='Reset.TButton', state=DISABLED, width=6)
        reset_button.grid(row=3, column=2, padx=0, pady=5, sticky="nsew")
        self.timers[i]['reset_button'] = reset_button

        stopped_time_label = ttk.Label(frame, text="Stopped at: --:--:--", font=("Helvetica", 12, 'italic'))
        stopped_time_label.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky="w")
        self.timers[i]['stopped_time_label'] = stopped_time_label

    def create_ranking_frame(self):
        self.ranking_frame = ttk.Frame(self.root, padding=5, relief=RIDGE, style='TFrame')
        self.ranking_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)
        self.ranking_frame.grid_rowconfigure(0, weight=1)
        self.ranking_frame.grid_columnconfigure(0, weight=1)

        self.ranking_label = ttk.Label(self.ranking_frame, text="Ranking:\n", font=("Helvetica", 16, 'bold'), background='#FFFFFF')
        self.ranking_label.pack(fill=BOTH, expand=True)

    def on_resize(self, event):
        # Resize the background image to fit the new window size
        new_width = self.root.winfo_width()
        new_height = self.root.winfo_height()
        
        if new_width != self.prev_width or new_height != self.prev_height:
            self.prev_width = new_width
            self.prev_height = new_height

            self.bg_image = self.bg_image.resize((new_width, new_height), Image.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(self.bg_image)
            self.canvas.itemconfig(self.bg_image_id, image=self.bg_photo)

            # Adjust font sizes dynamically
            max_font_size = 15  # Maximum font size to prevent scaling up on larger screens
            new_font_size = max(int(new_height / 100), max_font_size)  # Adjust divisor for optimal font scaling
            final_font_size = min(new_font_size, max_font_size)
            self.root.style.configure('TLabel', font=("Helvetica", final_font_size))
            self.root.style.configure('Stop.TButton', font=("Helvetica", final_font_size, 'bold'))
            self.root.style.configure('Reset.TButton', font=("Helvetica", final_font_size, 'bold'))
            self.root.style.configure('Set.TButton', font=("Helvetica", final_font_size, 'bold'))
            self.root.style.configure('Start.TButton', font=("Helvetica", final_font_size, 'bold'))

            # Adjust padding dynamically
            new_padding = max(int(new_height / 300), 2)  # Adjust divisor for optimal padding scaling
            self.root.style.configure('Stop.TButton', padding=new_padding)
            self.root.style.configure('Reset.TButton', padding=new_padding)
            self.root.style.configure('Set.TButton', padding=new_padding)
            self.root.style.configure('Start.TButton', padding=new_padding)

            # Adjust frame padding and widget sizes
            for timer in self.timers:
                frame = timer['frame']
                frame['padding'] = new_padding
                frame.grid_configure(padx=new_padding, pady=new_padding)
                
                for widget in frame.winfo_children():
                    # Limit entry and button widths to fit smaller screens
                    if isinstance(widget, tk.Entry) or isinstance(widget, ttk.Button):
                        widget.configure(width=max(int(new_width / 300), 3))  # Adjust divisor for optimal width scaling
                    widget.grid_configure(padx=new_padding, pady=new_padding)


    def exit_fullscreen(self, event=None):
        self.root.attributes('-fullscreen', False)

    def bind_keys(self):
        # Bind keys 1-9 to stop timers for channels 1-9
        for i in range(9):
            self.root.bind(str(i + 1), lambda event, idx=i: self.stop_timer(idx))

        # Bind key 0 to stop timer for channel 10
        self.root.bind('0', lambda event: self.stop_timer(9))

    def set_all_timers(self):
        for i in range(self.channels):
            self.timers[i]['minutes'].set(self.master_timer['minutes'].get())
            self.timers[i]['seconds'].set(self.master_timer['seconds'].get())
            self.timers[i]['milliseconds'].set(self.master_timer['milliseconds'].get())

    def start_all_timers(self):
        for i in range(self.channels):
            if not self.timers[i]['running']:
                self.start_timer(i)

    def start_timer(self, index):
        if not self.timers[index]['running']:
            total_seconds = (
                self.timers[index]['minutes'].get() * 60 +
                self.timers[index]['seconds'].get() +
                self.timers[index]['milliseconds'].get() / 10.0
            )
            self.timers[index]['remaining_time'] = total_seconds
            self.timers[index]['running'] = True
            self.timers[index]['paused'] = False
            self.timers[index]['count_thread'] = threading.Thread(target=lambda: self.run_timer(index))
            self.timers[index]['count_thread'].start()
            self.timers[index]['start_button'].config(state=tk.DISABLED)
            self.timers[index]['stop_button'].config(state=tk.NORMAL)
            self.timers[index]['reset_button'].config(state=tk.NORMAL)

    def run_timer(self, index):
        while self.timers[index]['remaining_time'] > 0:
            if not self.timers[index]['running']:
                break
            if self.timers[index]['paused']:
                continue
            time.sleep(0.1)
            self.timers[index]['remaining_time'] -= 0.1
            self.update_display(index)

        self.timers[index]['running'] = False
        self.update_display(index)
        if not self.timers[index]['paused']:
            messagebox.showinfo("Countdown Finished", f"Channel {index + 1}: Time's up!")
        self.timers[index]['start_button'].config(state=tk.NORMAL)
        self.timers[index]['stop_button'].config(state=tk.DISABLED)
        self.timers[index]['reset_button'].config(state=tk.DISABLED)

    def stop_timer(self, index):
        if self.timers[index]['running']:
            self.timers[index]['paused'] = True
            self.timers[index]['running'] = False
            self.timers[index]['stopped_time'] = self.timers[index]['remaining_time']
            self.timers[index]['stopped_time_label'].config(text=f"Stopped at: {self.format_time(index)}")
            self.timers[index]['start_button'].config(state=tk.NORMAL)
            self.timers[index]['stop_button'].config(state=tk.DISABLED)
            self.timers[index]['reset_button'].config(state=tk.NORMAL)

            # Add stopped time to the list and update ranking
            self.stopped_times.append((index + 1, self.timers[index]['stopped_time']))
            self.update_ranking()

    def reset_all_timers(self):
        for i in range(self.channels):
            self.reset_timer(i)
        self.stopped_times.clear()
        self.update_ranking()

    def reset_timer(self, index):
        self.timers[index]['running'] = False
        self.timers[index]['paused'] = False
        self.timers[index]['remaining_time'] = 0
        self.timers[index]['minutes'].set(0)
        self.timers[index]['seconds'].set(0)
        self.timers[index]['milliseconds'].set(0)
        self.update_display(index)
        self.timers[index]['start_button'].config(state=tk.NORMAL)
        self.timers[index]['stop_button'].config(state=tk.DISABLED)
        self.timers[index]['reset_button'].config(state=tk.DISABLED)
        self.timers[index]['stopped_time_label'].config(text="Stopped at: --:--:-")

    def update_display(self, index):
        mins = int(self.timers[index]['remaining_time'] / 60)
        secs = int(self.timers[index]['remaining_time'] % 60)
        millis = int((self.timers[index]['remaining_time'] - int(self.timers[index]['remaining_time'])) * 10)
        self.timers[index]['minutes'].set(mins)
        self.timers[index]['seconds'].set(secs)
        self.timers[index]['milliseconds'].set(millis)

    def format_time(self, index):
        mins = int(self.timers[index]['remaining_time'] / 60)
        secs = int(self.timers[index]['remaining_time'] % 60)
        millis = int((self.timers[index]['remaining_time'] - int(self.timers[index]['remaining_time'])) * 10)
        return f"{mins:02}:{secs:02}:{millis:01}"

    def update_ranking(self):
        self.stopped_times.sort(key=lambda x: x[1], reverse=True)
        ranking_text = "Ranking:\n"
        for rank, (team, time) in enumerate(self.stopped_times, start=1):
            mins = int(time / 60)
            secs = int(time % 60)
            millis = int((time - int(time)) * 10)
            formatted_time = f"{mins:02}:{secs:02}:{millis:01}"
            ranking_text += f"{rank}. Team {team}: {formatted_time}\n"
        self.ranking_label.config(text=ranking_text)

if __name__ == "__main__":
    root = tk.Tk()
    app = CountdownTimer(root, channels=10, initial_width=1000, initial_height=1000)
    root.mainloop()