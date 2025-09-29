import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import socketio
import threading
import json
import signal
import sys
from datetime import datetime
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    print("⚠️ System tray not available - install with: pip install pystray Pillow")

class AbletonCopilotGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("💫 Profesor Ableton 🎵")
        self.root.geometry("500x600")
        self.root.configure(bg='#ff6b35')  # Comic book orange background
        
        # Ensure window appears in taskbar and stays visible
        self.root.lift()
        self.root.focus_force()
        self.root.attributes('-topmost', True)
        self.root.after(100, lambda: self.root.attributes('-topmost', False))
        
        # SocketIO client
        self.sio = socketio.SimpleClient()
        self.connected = False
        
        # Current AI model
        self.current_model = "groq"
        
        # Question history
        self.history = []
        
        # System tray
        self.tray_icon = None
        self.is_hidden = False
        
        # Setup signal handling
        self.setup_signal_handlers()
        
        self.setup_ui()
        self.setup_tray()
        self.connect_to_server()
    
    def setup_signal_handlers(self):
        """Setup signal handlers to ignore Ctrl+C."""
        def signal_handler(sig, frame):
            print("\\nCtrl+C detected! Use the X button or File->Exit to close the application.")
            self.add_output("⚠️ Ctrl+C ignored - use X button to close", "system")
        
        # Handle Ctrl+C gracefully
        signal.signal(signal.SIGINT, signal_handler)
    
    def create_tray_icon(self):
        """Create a simple icon for system tray."""
        # Create a simple 64x64 icon
        image = Image.new('RGB', (64, 64), color='#2b2b2b')
        draw = ImageDraw.Draw(image)
        
        # Draw a simple music note
        draw.ellipse([20, 20, 44, 44], fill='#0066cc')
        draw.text((26, 26), "♪", fill='white')
        
        return image
    
    def setup_tray(self):
        """Setup system tray icon."""
        if not TRAY_AVAILABLE:
            return
            
        try:
            icon_image = self.create_tray_icon()
            
            # Create menu
            menu = pystray.Menu(
                pystray.MenuItem("Show Window", self.show_window),
                pystray.MenuItem("Hide Window", self.hide_window),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Exit", self.quit_application)
            )
            
            # Create tray icon
            self.tray_icon = pystray.Icon(
                "Profesor Ableton",
                icon_image,
                "💫 Profesor Ableton 🎵",
                menu
            )
            
            # Start tray in background thread
            tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            tray_thread.start()
            
            print("OK System tray icon created")
            
        except Exception as e:
            print(f"ERROR Failed to create system tray: {e}")
        
    def setup_ui(self):
        """Setup user interface."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Header
        header_frame = tk.Frame(self.root, bg='#ff1744', height=60)  # Comic book red header
        header_frame.pack(fill='x', padx=5, pady=(5,0))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="🎸 PROFESOR ABLETON 🎵", 
                              font=('Comic Sans MS', 18, 'bold'), 
                              fg='#ffff00', bg='#ff1744')  # Yellow text on red background
        title_label.pack(pady=10)
        
        # Status
        self.status_label = tk.Label(header_frame, text="🔴 Disconnected", 
                                   font=('Arial', 10), 
                                   fg='#ffff00', bg='#ff1744')
        self.status_label.pack()
        
        # Input section
        input_frame = tk.Frame(self.root, bg='#4caf50')  # Comic book green
        input_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(input_frame, text="🗨️ Ask Profesor Ableton:", 
                font=('Comic Sans MS', 12, 'bold'), 
                fg='#ffffff', bg='#4caf50').pack(anchor='w')
        
        # Input with autocomplete
        self.question_var = tk.StringVar()
        self.question_entry = tk.Entry(input_frame, 
                                     textvariable=self.question_var,
                                     font=('Arial', 11),
                                     bg='#404040', fg='white',
                                     insertbackground='white',
                                     relief='flat', bd=5)
        self.question_entry.pack(fill='x', pady=(5, 10), ipady=8)
        self.question_entry.bind('<Return>', self.send_question)
        self.question_entry.bind('<Up>', self.previous_question)
        self.question_entry.bind('<Down>', self.next_question)
        
        # Model selector
        model_frame = tk.Frame(input_frame, bg='#4caf50')
        model_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(model_frame, text="🧠 AI Brain:", 
                font=('Comic Sans MS', 10, 'bold'), 
                fg='#ffffff', bg='#4caf50').pack(side='left')
        
        self.model_var = tk.StringVar(value="groq")
        self.model_selector = ttk.Combobox(model_frame, 
                                         textvariable=self.model_var,
                                         values=["groq", "grok (xAI)", "claude", "openai", "ollama"],
                                         state="readonly",
                                         width=15)
        self.model_selector.pack(side='left', padx=(10, 0))
        self.model_selector.bind('<<ComboboxSelected>>', self.on_model_change)
        
        # Global keyboard shortcuts
        self.root.bind('<Control-h>', lambda e: self.hide_window())
        self.root.bind('<Control-s>', lambda e: self.show_window())
        self.root.bind('<Escape>', lambda e: self.hide_window())
        
        # Buttons
        button_frame = tk.Frame(input_frame, bg='#2b2b2b')
        button_frame.pack(fill='x')
        
        self.ask_button = tk.Button(button_frame, text="Ask AI >>", 
                                  command=self.send_question,
                                  font=('Arial', 11, 'bold'),
                                  bg='#0066cc', fg='white',
                                  relief='flat', bd=0, padx=20, pady=5)
        self.ask_button.pack(side='left')
        
        tk.Button(button_frame, text="Clear 🗑️", 
                 command=self.clear_output,
                 font=('Arial', 10),
                 bg='#666666', fg='white',
                 relief='flat', bd=0, padx=15, pady=5).pack(side='right')
        
        # Output section
        output_frame = tk.Frame(self.root, bg='#2b2b2b')
        output_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        tk.Label(output_frame, text="AI Responses:", 
                font=('Arial', 12, 'bold'), 
                fg='white', bg='#2b2b2b').pack(anchor='w')
        
        # Scrollable text area
        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            font=('Consolas', 10),
            bg='#1a1a1a', fg='#e0e0e0',
            insertbackground='white',
            relief='flat', bd=5,
            wrap=tk.WORD,
            state='disabled'
        )
        self.output_text.pack(fill='both', expand=True, pady=(5, 0))
        
        # Quick questions
        quick_frame = tk.Frame(self.root, bg='#2b2b2b')
        quick_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        tk.Label(quick_frame, text="Quick questions:", 
                font=('Arial', 10, 'bold'), 
                fg='white', bg='#2b2b2b').pack(anchor='w')
        
        quick_buttons_frame = tk.Frame(quick_frame, bg='#2b2b2b')
        quick_buttons_frame.pack(fill='x', pady=(5, 0))
        
        quick_questions = [
            "What is EQ?",
            "How to use compressor?",
            "Explain reverb",
            "Tempo automation"
        ]
        
        for i, question in enumerate(quick_questions):
            btn = tk.Button(quick_buttons_frame, text=question,
                          command=lambda q=question: self.set_question(q),
                          font=('Arial', 9),
                          bg='#444444', fg='white',
                          relief='flat', bd=0, padx=10, pady=3)
            btn.pack(side='left', padx=(0, 5))
        
        # Bottom controls
        bottom_frame = tk.Frame(self.root, bg='#2b2b2b')
        bottom_frame.pack(fill='x', padx=10, pady=(0, 5))
        
        # Always on top checkbox
        self.always_on_top = tk.BooleanVar()
        tk.Checkbutton(bottom_frame, text="Always on top", 
                      variable=self.always_on_top,
                      command=self.toggle_always_on_top,
                      font=('Arial', 9),
                      fg='white', bg='#2b2b2b',
                      selectcolor='#404040').pack(side='left')
        
        # Control buttons
        if TRAY_AVAILABLE:
            tk.Button(bottom_frame, text="Hide to Tray", 
                     command=self.minimize_window,
                     font=('Arial', 9),
                     bg='#444444', fg='white',
                     relief='flat', bd=0, padx=10, pady=2).pack(side='right', padx=(5,0))
        else:
            tk.Button(bottom_frame, text="Minimize", 
                     command=self.minimize_window,
                     font=('Arial', 9),
                     bg='#444444', fg='white',
                     relief='flat', bd=0, padx=10, pady=2).pack(side='right', padx=(5,0))
        
        # Focus on input
        self.question_entry.focus()
        
    def connect_to_server(self):
        """Connect to Copilot server."""
        def connect():
            # Try multiple ports in case server is running on different port
            ports_to_try = [12345, 12346, 12347, 12348, 12349]
            
            for port in ports_to_try:
                try:
                    print(f"Trying to connect to localhost:{port}")
                    self.sio.connect(f'http://localhost:{port}')
                    self.connected = True
                    self.root.after(0, self.update_status, ">> Connected")
                    self.add_output(f"🎵 GROOVY! Profesor Ableton is online on port {port}!", "system")
                    return
                except Exception as e:
                    print(f"Failed to connect to port {port}: {e}")
                    continue
            
            # If we get here, all ports failed
            self.connected = False
            self.root.after(0, self.update_status, ">> Disconnected")
            self.add_output("😵 BUMMER! Can't find Profesor Ableton's server (ports 12345-12349)", "error")
        
        threading.Thread(target=connect, daemon=True).start()
    
    def update_status(self, status):
        """Update status label."""
        self.status_label.config(text=status)
        if "Connected" in status:
            self.status_label.config(fg='#44ff44')
        else:
            self.status_label.config(fg='#ff4444')
    
    def on_model_change(self, event=None):
        """Handle model selection change."""
        selected = self.model_var.get()
        
        # Map display names to internal names
        model_mapping = {
            "groq": "groq",
            "grok (xAI)": "grok", 
            "claude": "claude",
            "openai": "openai",
            "ollama": "ollama"
        }
        
        self.current_model = model_mapping.get(selected, "groq")
        
        # Show model change message
        model_names = {
            "groq": "Groq (Free, Fast)",
            "grok": "xAI Grok (Paid)",
            "claude": "Claude (Paid)", 
            "openai": "OpenAI (Paid)",
            "ollama": "Ollama (Local)"
        }
        
        model_display = model_names.get(self.current_model, self.current_model)
        self.add_output(f">> Switched to: {model_display}", "system")
    
    def send_question(self, event=None):
        """Send question to AI."""
        question = self.question_var.get().strip()
        if not question:
            return
            
        if not self.connected:
            messagebox.showerror("Error", "Not connected to server!")
            return
            
        # Add to history
        if question not in self.history:
            self.history.append(question)
        self.history_index = len(self.history)
        
        # Send question
        self.add_output(f"🔵 You: {question}", "user")
        self.question_var.set("")
        self.ask_button.config(state='disabled', text="Waiting...")
        
        def send():
            try:
                self.sio.emit('command', {
                    'action': 'ask_ai',
                    'params': {
                        'question': question,
                        'preferred_model': self.current_model
                    }
                })
                
                # Wait for response
                response = self.sio.receive(timeout=60)
                if response:
                    event, data = response
                    if event == 'response':
                        ai_response = data.get('message', 'No response')
                        self.root.after(0, self.add_output, f">> AI: {ai_response}", "ai")
                    else:
                        self.root.after(0, self.add_output, f"❓ Unexpected response: {data}", "error")
                else:
                    self.root.after(0, self.add_output, "TIMEOUT Timeout - no response", "error")
                    
            except Exception as e:
                self.root.after(0, self.add_output, f"ERROR Error: {e}", "error")
            finally:
                self.root.after(0, lambda: self.ask_button.config(state='normal', text="Ask AI >>"))
        
        threading.Thread(target=send, daemon=True).start()
    
    def add_output(self, text, msg_type="normal"):
        """Add text to output."""
        self.output_text.config(state='normal')
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_text = f"[{timestamp}] {text}\n\n"
        
        self.output_text.insert(tk.END, formatted_text)
        
        # Scroll to bottom
        self.output_text.see(tk.END)
        self.output_text.config(state='disabled')
    
    def clear_output(self):
        """Clear output."""
        self.output_text.config(state='normal')
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state='disabled')
    
    def set_question(self, question):
        """Set question in input."""
        self.question_var.set(question)
        self.question_entry.focus()
    
    def previous_question(self, event):
        """Previous questions with Up arrow."""
        if hasattr(self, 'history_index') and self.history:
            self.history_index = max(0, self.history_index - 1)
            if self.history_index < len(self.history):
                self.question_var.set(self.history[self.history_index])
    
    def next_question(self, event):
        """Next question with Down arrow."""
        if hasattr(self, 'history_index') and self.history:
            self.history_index = min(len(self.history), self.history_index + 1)
            if self.history_index < len(self.history):
                self.question_var.set(self.history[self.history_index])
            else:
                self.question_var.set("")
    
    def toggle_always_on_top(self):
        """Toggle always on top."""
        self.root.attributes('-topmost', self.always_on_top.get())
    
    def minimize_window(self):
        """Minimize to system tray."""
        if TRAY_AVAILABLE and self.tray_icon:
            self.hide_window()
        else:
            self.root.iconify()
    
    def show_window(self):
        """Show window from tray."""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.is_hidden = False
    
    def hide_window(self):
        """Hide window to tray."""
        if TRAY_AVAILABLE:
            self.root.withdraw()
            self.is_hidden = True
            if hasattr(self, 'output_text'):
                self.add_output("📍 Minimized to system tray - right-click tray icon to restore", "system")
        else:
            self.root.iconify()
    
    def quit_application(self):
        """Quit the entire application."""
        self.on_closing()
    
    def run(self):
        """Run GUI."""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Make sure window is visible at start
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        
        self.root.mainloop()
    
    def on_closing(self):
        """Cleanup on close."""
        if self.connected:
            try:
                self.sio.disconnect()
            except:
                pass
        
        # Stop tray icon
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except:
                pass
        
        self.root.destroy()

if __name__ == "__main__":
    print(" Starting Ableton AI Copilot GUI...")
    print(">> Make sure server is running: python copilot_server.py")
    
    app = AbletonCopilotGUI()
    app.run()