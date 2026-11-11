# auth/login_screen.py
import tkinter as tk
from tkinter import messagebox
import os
from PIL import Image, ImageTk, ImageOps
from config.settings import LIGHT_THEME, DARK_THEME, APP_NAME, APP_SETTINGS, save_theme_pref
from auth.login import authenticate_user

class LoginScreen:
    def __init__(self, app_instance, role, on_success):
        self.app = app_instance
        self.root = app_instance.root
        self.role = role
        self.on_success = on_success
        
        self.is_dark_mode = APP_SETTINGS['is_dark_mode']
        self.theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
        
        self.password_visible = False
        self.email_placeholder = "Username"
        self.pwd_placeholder = "Password"
        self.email_is_placeholder = True
        self.pwd_is_placeholder = True
        self.saved_email = ""
        self.saved_pwd = ""

        self.window = tk.Toplevel(self.root)
        self.window.title(f"{role.capitalize()} Sign In - {APP_NAME}")
        
        width = 1300
        height = 850
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        self.window.grab_set()
        self.window.resizable(False, False)
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        self.create_widgets()

    def toggle_theme(self):
        self.saved_email = self.email_entry.get()
        self.saved_pwd = self.pwd_entry.get()
        if self.email_is_placeholder: self.saved_email = ""
        if self.pwd_is_placeholder: self.saved_pwd = ""

        APP_SETTINGS['is_dark_mode'] = not APP_SETTINGS['is_dark_mode']
        save_theme_pref(APP_SETTINGS['is_dark_mode'])
        
        self.is_dark_mode = APP_SETTINGS['is_dark_mode']
        self.theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
        
        for widget in self.window.winfo_children():
            widget.destroy()
        self.create_widgets()

    def create_widgets(self):
        self.window.configure(bg=self.theme['bg_main'])
        
        main_frame = tk.Frame(self.window, bg=self.theme['bg_main'])
        main_frame.pack(fill='both', expand=True)

        left_frame = tk.Frame(main_frame, bg=self.theme['sidebar_bg'], width=650, height=850)
        left_frame.pack(side='left', fill='both')
        left_frame.pack_propagate(False)

        img_path = os.path.join("assets", "images", "login_bg.jpg")
        if os.path.exists(img_path):
            img = Image.open(img_path)
            img = ImageOps.fit(img, (650, 850), Image.Resampling.LANCZOS)
            self.bg_image = ImageTk.PhotoImage(img)
            img_label = tk.Label(left_frame, image=self.bg_image, bg=self.theme['sidebar_bg'])
            img_label.pack(fill='both', expand=True)
        else:
            tk.Label(left_frame, text="[ Image Missing ]\n\nPlace 'login_bg.jpg'\nin assets/images/", 
                     font=("Segoe UI", 14), bg=self.theme['sidebar_bg'], fg="white").pack(expand=True)

        right_frame = tk.Frame(main_frame, bg=self.theme['bg_main'], width=650, height=850)
        right_frame.pack(side='right', fill='both')
        right_frame.pack_propagate(False)

        moon_icon = "☀" if self.is_dark_mode else "☾"
        tk.Button(right_frame, text=moon_icon, font=("Segoe UI", 24), bg=self.theme['bg_main'], fg=self.theme['text_main'],
                  relief="flat", cursor="hand2", command=self.toggle_theme).place(relx=1.0, rely=0.0, x=-30, y=30, anchor='ne')

        form_card = tk.Frame(right_frame, bg=self.theme['bg_main'])
        form_card.place(relx=0.5, rely=0.5, anchor='center')

        brand_row = tk.Frame(form_card, bg=self.theme['bg_main'])
        brand_row.pack(pady=(0, 5))
        
        tk.Label(brand_row, text="☕", font=("Segoe UI Emoji", 56), bg=self.theme['bg_main'], fg=self.theme['accent']).pack(side='left', padx=(0, 15))
        
        brand_text = tk.Frame(brand_row, bg=self.theme['bg_main'])
        brand_text.pack(side='left')
        
        txt_row = tk.Frame(brand_text, bg=self.theme['bg_main'])
        txt_row.pack(anchor='w')
        tk.Label(txt_row, text="Byte ", font=("Segoe UI", 26, "bold"), bg=self.theme['bg_main'], fg=self.theme['text_main']).pack(side='left')
        tk.Label(txt_row, text="& Brew", font=("Segoe UI", 26, "bold"), bg=self.theme['bg_main'], fg=self.theme['accent']).pack(side='left')

        tk.Label(brand_text, text="C O F F E E   •   C O D E   •   C R E A T E", font=("Segoe UI", 8, "bold"), 
                 bg=self.theme['bg_main'], fg=self.theme['text_muted']).pack(anchor='w')

        portal_title = "Admin Portal" if self.role.lower() == "admin" else "Cashier Portal"
        portal_subtitle = "Log in to continue to your Admin Dashboard." if self.role.lower() == "admin" else "Log in to continue to your POS."
        
        tk.Label(form_card, text=portal_title, font=("Segoe UI", 20, "bold"), bg=self.theme['bg_main'], fg=self.theme['text_main']).pack(pady=(30, 5))
        tk.Label(form_card, text=portal_subtitle, font=("Segoe UI", 11), bg=self.theme['bg_main'], fg=self.theme['text_muted']).pack(pady=(0, 30))

        def create_input_frame(icon_text):
            frame = tk.Frame(form_card, bg=self.theme['bg_card'], highlightbackground=self.theme['border'], highlightthickness=1)
            frame.pack(fill='x', pady=10)
            tk.Label(frame, text=icon_text, font=("Segoe UI", 14), bg=self.theme['bg_card'], fg=self.theme['text_muted']).pack(side='left', padx=(20, 10), pady=15)
            return frame

        email_frame = create_input_frame("👤")
        self.email_entry = tk.Entry(email_frame, font=("Segoe UI", 13), bg=self.theme['bg_card'], fg=self.theme['text_muted'], 
                                    relief="flat", insertbackground=self.theme['text_main'])
        self.email_entry.pack(side='left', fill='x', expand=True, padx=(5, 20), pady=15)
        
        if self.saved_email:
            self.email_entry.insert(0, self.saved_email)
            self.email_entry.config(fg=self.theme['text_main'])
            self.email_is_placeholder = False
        else:
            self.email_entry.insert(0, self.email_placeholder)
            self.email_entry.config(fg=self.theme['text_muted'])
            self.email_is_placeholder = True

        self.email_entry.bind('<FocusIn>', self.on_email_focus_in)
        self.email_entry.bind('<FocusOut>', self.on_email_focus_out)

        pwd_frame = create_input_frame("🔒")
        self.pwd_entry = tk.Entry(pwd_frame, font=("Segoe UI", 13), bg=self.theme['bg_card'], fg=self.theme['text_muted'], 
                                  relief="flat", insertbackground=self.theme['text_main'])
        self.pwd_entry.pack(side='left', fill='x', expand=True, padx=(5, 5), pady=15)

        if self.saved_pwd:
            self.pwd_entry.insert(0, self.saved_pwd)
            self.pwd_entry.config(fg=self.theme['text_main'])
            if not self.password_visible:
                self.pwd_entry.config(show="•")
            self.pwd_is_placeholder = False
        else:
            self.pwd_entry.config(show="")
            self.pwd_entry.insert(0, self.pwd_placeholder)
            self.pwd_entry.config(fg=self.theme['text_muted'])
            self.pwd_is_placeholder = True

        self.pwd_entry.bind('<FocusIn>', self.on_pwd_focus_in)
        self.pwd_entry.bind('<FocusOut>', self.on_pwd_focus_out)

        self.eye_btn = tk.Button(pwd_frame, text="👁", font=("Segoe UI", 14), bg=self.theme['bg_card'], fg=self.theme['text_muted'], 
                                 relief="flat", cursor="hand2", command=self.toggle_password)
        self.eye_btn.pack(side='right', padx=(5, 20))

        sign_in_btn = tk.Button(form_card, text="Sign In", font=("Segoe UI", 14, "bold"), 
                                bg=self.theme['accent'], fg=self.theme['accent_fg'], activebackground=self.theme['accent_hover'], activeforeground=self.theme['accent_fg'],
                                relief="flat", cursor="hand2", command=self.attempt_login)
        sign_in_btn.pack(fill='x', pady=(40, 20), ipady=12)

        tk.Label(form_card, text="Need help? Contact your admin.", font=("Segoe UI", 10), bg=self.theme['bg_main'], fg=self.theme['text_muted']).pack(pady=(10, 0))

        self.window.bind('<Return>', lambda e: self.attempt_login())

    def on_email_focus_in(self, event):
        if self.email_is_placeholder:
            self.email_entry.delete(0, 'end')
            self.email_entry.config(fg=self.theme['text_main'])
            self.email_is_placeholder = False

    def on_email_focus_out(self, event):
        if not self.email_entry.get():
            self.email_entry.insert(0, self.email_placeholder)
            self.email_entry.config(fg=self.theme['text_muted'])
            self.email_is_placeholder = True

    def on_pwd_focus_in(self, event):
        if self.pwd_is_placeholder:
            self.pwd_entry.delete(0, 'end')
            self.pwd_entry.config(fg=self.theme['text_main'])
            if not self.password_visible:
                self.pwd_entry.config(show="•")
            self.pwd_is_placeholder = False

    def on_pwd_focus_out(self, event):
        if not self.pwd_entry.get():
            self.pwd_entry.config(show="") 
            self.pwd_entry.insert(0, self.pwd_placeholder)
            self.pwd_entry.config(fg=self.theme['text_muted'])
            self.pwd_is_placeholder = True

    def toggle_password(self):
        if self.pwd_is_placeholder:
            return

        if self.password_visible:
            self.pwd_entry.config(show="•")
            self.eye_btn.config(fg=self.theme['text_muted'])
            self.password_visible = False
        else:
            self.pwd_entry.config(show="")
            self.eye_btn.config(fg=self.theme['accent'])
            self.password_visible = True

    def on_close(self):
        self.window.destroy()
        if hasattr(self.app, 'refresh_theme'):
            self.app.refresh_theme()
        else:
            self.root.deiconify()

    def attempt_login(self):
        email = "" if self.email_is_placeholder else self.email_entry.get().strip()
        password = "" if self.pwd_is_placeholder else self.pwd_entry.get()

        if not email or not password:
            messagebox.showerror("Error", "Please enter both email and password.", parent=self.window)
            return

        success, message, user_data = authenticate_user(email, password, self.role)

        if success:
            self.window.destroy()
            self.on_success(user_data)
        else:
            messagebox.showerror("Login Failed", message, parent=self.window)