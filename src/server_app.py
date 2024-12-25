import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import logging

class ServerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Server Control Panel")

        # Create a container for pages
        self.container = tk.Frame(self.root)
        self.container.pack(fill="both", expand=True)

        # Dictionary to hold pages
        self.pages = {}

        # Initialize pages
        self.create_login_page()
        self.create_control_page()
        self.create_log_page()

        # Show the login page initially
        self.show_page("Login")

        # Logger setup
        self.logger = logging.getLogger("ServerApp")
        self.logger.setLevel(logging.INFO)
        self.log_handler = TextHandler(self.pages["Log"].log_text)
        self.logger.addHandler(self.log_handler)

    def create_login_page(self):
        frame = LoginPage(self.container, self.show_page)
        self.pages["Login"] = frame
        frame.grid(row=0, column=0, sticky="nsew")

    def create_control_page(self):
        frame = ControlPage(self.container, self.show_page, self.start_server)
        self.pages["Control"] = frame
        frame.grid(row=0, column=0, sticky="nsew")

    def create_log_page(self):
        frame = LogPage(self.container, self.show_page)
        self.pages["Log"] = frame
        frame.grid(row=0, column=0, sticky="nsew")

    def show_page(self, page_name):
        page = self.pages[page_name]
        page.tkraise()

    def start_server(self):
        threading.Thread(target=self.run_server, daemon=True).start()

    def run_server(self):
        self.logger.info("Starting server...")


class LoginPage(tk.Frame):
    def __init__(self, parent, show_page):
        super().__init__(parent)
        self.show_page = show_page

        tk.Label(self, text="Username:").pack(pady=5)
        self.username_entry = tk.Entry(self)
        self.username_entry.pack(pady=5)

        tk.Label(self, text="Password:").pack(pady=5)
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack(pady=5)

        self.error_label = tk.Label(self, text="", fg="red")
        self.error_label.pack()

        tk.Button(self, text="Login", command=self.validate_login).pack(pady=10)

    def validate_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if username == "admin" and password == "admin":
            self.show_page("Control")
        else:
            self.error_label.config(text="Invalid username or password")


class ControlPage(tk.Frame):
    def __init__(self, parent, show_page, start_server_callback):
        super().__init__(parent)
        self.show_page = show_page
        self.start_server_callback = start_server_callback

        tk.Label(self, text="Server Control Panel", font=("Arial", 16)).pack(pady=10)

        self.start_button = tk.Button(self, text="Start Server", command=self.start_server)
        self.start_button.pack(pady=10)

        tk.Button(self, text="View Logs", command=lambda: self.show_page("Log")).pack(pady=10)

    def start_server(self):
        self.start_server_callback()


class LogPage(tk.Frame):
    def __init__(self, parent, show_page):
        super().__init__(parent)
        self.show_page = show_page

        tk.Label(self, text="Server Logs", font=("Arial", 16)).pack(pady=10)

        self.log_text = scrolledtext.ScrolledText(self, state="disabled", height=15)
        self.log_text.pack(fill="both", expand=True, pady=10, padx=10)

        tk.Button(self, text="Back", command=lambda: self.show_page("Control")).pack(pady=10)


class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        self.text_widget.configure(state="normal")
        self.text_widget.insert("end", msg + "\n")
        self.text_widget.configure(state="disabled")
        self.text_widget.see("end")


def start_gui():
    root = tk.Tk()
    app = ServerApp(root)
    root.mainloop()
