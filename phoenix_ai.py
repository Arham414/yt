import os
import json
import pyttsx3
import requests
import threading
import pyautogui
import pytesseract
import subprocess
import speech_recognition as sr
from PIL import Image
import PyPDF2
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import webbrowser

# ======= SETUP =======
MEMORY_FILE = "phoenix_memory.json"
THEME = {"bg": "#1e1e1e", "fg": "#ffffff", "entry": "#2b2b2b", "light_bg": "#ffffff", "light_fg": "#000000"}
is_dark = True

# ======= TEXT TO SPEECH =======
engine = pyttsx3.init()
engine.setProperty('rate', 180)

def speak(text):
    engine.say(text)
    engine.runAndWait()

# ======= VOICE TO TEXT =======
def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Listening...")
        audio = r.listen(source)
    try:
        return r.recognize_google(audio).lower()
    except:
        return "Sorry, I didn't catch that."

# ======= IMAGE/PDF READER =======
def read_pdf(path):
    with open(path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])

def read_image(path):
    img = Image.open(path)
    return pytesseract.image_to_string(img)

# ======= LOCAL MODEL =======
def query_local_model(prompt):
    try:
        res = requests.post("http://localhost:11434/api/generate", json={
            "model": "mistral",
            "prompt": prompt,
            "stream": False
        })
        return res.json()["response"]
    except:
        return None

# ======= GOOGLE FALLBACK =======
def fallback_search(prompt):
    webbrowser.open(f"https://www.google.com/search?q={prompt}")
    return "I couldn't answer. Here's a Google search instead."

# ======= MEMORY MANAGEMENT =======
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r') as f:
            return json.load(f)
    return []

def save_memory(memory):
    with open(MEMORY_FILE, 'w') as f:
        json.dump(memory, f, indent=2)

# ======= APP COMMANDS =======
def execute_command(text):
    text = text.lower()
    if "open" in text:
        app = text.replace("open", "").strip()
        subprocess.Popen(f"{app}.exe", shell=True)
        return f"Opening {app}..."
    elif "type" in text:
        msg = text.replace("type", "").strip()
        pyautogui.write(msg)
        return f"Typing: {msg}"
    elif "click" in text:
        pyautogui.click()
        return "Clicked."
    elif "shutdown" in text:
        os.system("shutdown /s /t 1")
        return "Shutting down..."
    elif "restart" in text:
        os.system("shutdown /r /t 1")
        return "Restarting..."
    else:
        response = query_local_model(text)
        if not response:
            return fallback_search(text)
        return response

# ======= GUI CLASS =======
class PhoenixApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🔥 Phoenix AI Assistant")
        self.root.geometry("800x600")
        self.memory = load_memory()
        self.setup_gui()
        self.apply_theme()

    def setup_gui(self):
        self.chat = scrolledtext.ScrolledText(self.root, font=("Consolas", 12))
        self.chat.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.entry = tk.Entry(self.root, font=("Arial", 14))
        self.entry.pack(padx=10, pady=5, fill=tk.X)
        self.entry.bind("<Return>", self.send_input)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack()

        tk.Button(btn_frame, text="🎤 Voice", command=self.voice_input).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="📄 PDF", command=self.load_pdf).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🖼️ Image", command=self.load_image).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🌓 Toggle Theme", command=self.toggle_theme).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🧠 History", command=self.show_history).pack(side=tk.LEFT, padx=5)

        self.chat.insert(tk.END, "Phoenix: Hello, I am Phoenix — your offline AI assistant 🔥\n\n")

    def apply_theme(self):
        global is_dark
        theme = THEME if is_dark else {
            "bg": THEME["light_bg"],
            "fg": THEME["light_fg"],
            "entry": THEME["light_bg"]
        }
        self.root.config(bg=theme["bg"])
        self.chat.config(bg=theme["bg"], fg=theme["fg"], insertbackground=theme["fg"])
        self.entry.config(bg=theme["entry"], fg=theme["fg"], insertbackground=theme["fg"])

    def toggle_theme(self):
        global is_dark
        is_dark = not is_dark
        self.apply_theme()

    def voice_input(self):
        def run():
            text = listen()
            self.entry.delete(0, tk.END)
            self.entry.insert(0, text)
            self.send_input()
        threading.Thread(target=run).start()

    def send_input(self, event=None):
        prompt = self.entry.get().strip()
        if not prompt:
            return
        self.entry.delete(0, tk.END)
        self.chat.insert(tk.END, f"You: {prompt}\n")

        def process():
            response = execute_command(prompt)
            self.chat.insert(tk.END, f"Phoenix: {response}\n\n")
            speak(response)
            self.memory.append({"you": prompt, "phoenix": response})
            save_memory(self.memory)

        threading.Thread(target=process).start()

    def load_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if path:
            text = read_pdf(path)
            self.chat.insert(tk.END, f"[PDF]:\n{text}\n\n")

    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if path:
            text = read_image(path)
            self.chat.insert(tk.END, f"[Image]:\n{text}\n\n")

    def show_history(self):
        history = "\n".join([f"You: {m['you']}\nPhoenix: {m['phoenix']}\n" for m in self.memory])
        messagebox.showinfo("Chat History", history or "No history found.")

# ======= RUN PHOENIX =======
if __name__ == "__main__":
    root = tk.Tk()
    app = PhoenixApp(root)
    root.mainloop()
