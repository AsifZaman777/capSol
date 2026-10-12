"""
==============================================================================
FILE HISTORY CARD
------------------------------------------------------------------------------
File:           popup.py
Author:         Asif Zaman
Created:        2026-10-12
Responsibility: User interface layer providing a Tkinter modal dialog. Collects
                target website URL, login ID, and password securely with masking
                and show/hide toggling before triggering the automation flow.
==============================================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv

class CredentialPopup:
    """
    Modern modal dialog for entering target URL and credentials.
    Pre-populates values from .env if present.
    """
    def __init__(self, default_url: Optional[str] = None):
        load_dotenv('.env')
        self.default_url = default_url or "https://merchant.sslcommerz.com/?request=dTFyQWlsb2dpbjp2aWV3dTFyQWk%3D&id=dTFyQWkxdTFyQWk%3D"
        self.env_user = os.getenv("MERCHANT_ID", "")
        self.env_pass = os.getenv("MERCHANT_PASSWORD", "")
        self.result: Optional[Dict[str, Any]] = None

    def show(self) -> Optional[Dict[str, Any]]:
        """Displays popup modal and returns user inputs or None if canceled."""
        root = tk.Tk()
        root.title("Auto Login Framework")
        root.geometry("520x460")
        root.resizable(False, False)

        # Center on screen
        root.update_idletasks()
        w, h = 520, 460
        x = (root.winfo_screenwidth() // 2) - (w // 2)
        y = (root.winfo_screenheight() // 2) - (h // 2)
        root.geometry(f"{w}x{h}+{x}+{y}")

        # Styles
        style = ttk.Style(root)
        style.theme_use("clam")
        bg_color = "#f8f9fa"
        primary_color = "#2563eb"
        text_color = "#1e293b"

        root.configure(bg=bg_color)
        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color, foreground=text_color, font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 15, "bold"), foreground="#0f172a")
        style.configure("Sub.TLabel", font=("Segoe UI", 9), foreground="#64748b")
        style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), background=primary_color, foreground="white")
        style.map("Action.TButton", background=[("active", "#1d4ed8")])
        style.configure("Cancel.TButton", font=("Segoe UI", 10))

        main_frame = ttk.Frame(root, padding=24)
        main_frame.pack(fill="both", expand=True)

        # Header
        ttk.Label(main_frame, text="🚀 Web Login Automation", style="Header.TLabel").pack(anchor="w", pady=(0, 2))
        ttk.Label(main_frame, text="Enter the target URL and credentials to begin auto-login.", style="Sub.TLabel").pack(anchor="w", pady=(0, 16))

        # Target URL
        ttk.Label(main_frame, text="Target Website URL:").pack(anchor="w", pady=(4, 2))
        url_var = tk.StringVar(value=self.default_url)
        ttk.Entry(main_frame, textvariable=url_var, font=("Segoe UI", 10)).pack(fill="x", pady=(0, 10))

        # Username
        ttk.Label(main_frame, text="Username / Login ID / Email:").pack(anchor="w", pady=(4, 2))
        user_var = tk.StringVar(value=self.env_user)
        user_entry = ttk.Entry(main_frame, textvariable=user_var, font=("Segoe UI", 10))
        user_entry.pack(fill="x", pady=(0, 10))

        # Password
        ttk.Label(main_frame, text="Password:").pack(anchor="w", pady=(4, 2))
        pass_var = tk.StringVar(value=self.env_pass)
        pass_frame = ttk.Frame(main_frame)
        pass_frame.pack(fill="x", pady=(0, 10))

        pass_entry = ttk.Entry(pass_frame, textvariable=pass_var, show="•", font=("Segoe UI", 10))
        pass_entry.pack(side="left", fill="x", expand=True)

        show_pass = tk.BooleanVar(value=False)
        def toggle_password():
            if show_pass.get():
                pass_entry.config(show="")
                show_btn.config(text="🙈 Hide")
            else:
                pass_entry.config(show="•")
                show_btn.config(text="👁 Show")

        show_btn = tk.Button(
            pass_frame, text="👁 Show", font=("Segoe UI", 9), relief="groove",
            command=lambda: [show_pass.set(not show_pass.get()), toggle_password()]
        )
        show_btn.pack(side="right", padx=(6, 0))

        # Options
        captcha_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="Auto-detect & solve CAPTCHA with TrOCR", variable=captcha_var).pack(anchor="w", pady=(4, 16))

        # Actions
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", side="bottom")

        def on_submit():
            url = url_var.get().strip()
            username = user_var.get().strip()
            password = pass_var.get().strip()

            if not url:
                messagebox.showerror("Validation Error", "Please provide a target URL.", parent=root)
                return
            if not username or not password:
                messagebox.showerror("Validation Error", "Please enter both username and password.", parent=root)
                return

            self.result = {
                "url": url,
                "username": username,
                "password": password,
                "auto_captcha": captcha_var.get()
            }
            root.destroy()

        def on_cancel():
            self.result = None
            root.destroy()

        root.bind("<Return>", lambda event: on_submit())
        root.bind("<Escape>", lambda event: on_cancel())

        submit_btn = ttk.Button(btn_frame, text="Start Auto-Login →", style="Action.TButton", command=on_submit)
        submit_btn.pack(side="right", padx=(8, 0), ipadx=8, ipady=4)

        cancel_btn = ttk.Button(btn_frame, text="Cancel", style="Cancel.TButton", command=on_cancel)
        cancel_btn.pack(side="right", ipady=4)

        # Focus
        if not user_var.get():
            user_entry.focus_set()
        elif not pass_var.get():
            pass_entry.focus_set()
        else:
            submit_btn.focus_set()

        root.mainloop()
        return self.result

def prompt_credentials(default_url: Optional[str] = None) -> Optional[Dict[str, Any]]:
    return CredentialPopup(default_url=default_url).show()

if __name__ == "__main__":
    print("Credentials entered:", prompt_credentials())
