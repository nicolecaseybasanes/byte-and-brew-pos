# main.py
import tkinter as tk
from tkinter import messagebox
import os
from PIL import Image, ImageTk, ImageOps
from config.settings import LIGHT_THEME, DARK_THEME, APP_TITLE, APP_SETTINGS, save_theme_pref
from auth.login_screen import LoginScreen
from admin.dashboard import AdminDashboard
from cashier.pos import CashierPOS

class RoleSelectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        
        self.is_dark_mode = APP_SETTINGS['is_dark_mode']
        self.theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
        
        width = 1300
        height = 850
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        self.root.resizable(False, False)
        self.create_widgets()

    def toggle_theme(self):
        APP_SETTINGS['is_dark_mode'] = not APP_SETTINGS['is_dark_mode']
        save_theme_pref(APP_SETTINGS['is_dark_mode'])
        self.refresh_theme()

    def refresh_theme(self):
        self.is_dark_mode = APP_SETTINGS['is_dark_mode']
        self.theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
        
        for widget in self.root.winfo_children():
            widget.destroy()
        self.create_widgets()

    def create_widgets(self):
        self.root.configure(bg=self.theme['bg_main'])
        
        main_frame = tk.Frame(self.root, bg=self.theme['bg_main'])
        main_frame.pack(fill='both', expand=True)

        left_frame = tk.Frame(main_frame, bg=self.theme['sidebar_bg'], width=650, height=850)
        left_frame.pack(side='left', fill='both')
        left_frame.pack_propagate(False)

        img_path = os.path.join("assets", "images", "role_bg.jpg")
        if os.path.exists(img_path):
            img = Image.open(img_path)
            img = ImageOps.fit(img, (650, 850), Image.Resampling.LANCZOS)
            self.bg_image = ImageTk.PhotoImage(img)
            img_label = tk.Label(left_frame, image=self.bg_image, bg=self.theme['sidebar_bg'])
            img_label.pack(fill='both', expand=True)
        else:
            tk.Label(left_frame, text="[ Image Missing ]\n\nPlace 'role_bg.jpg'\nin assets/images/", 
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
        
        tk.Label(brand_row, text="☕", font=("Segoe UI Emoji", 64), bg=self.theme['bg_main'], fg=self.theme['accent']).pack(side='left', padx=(0, 15))
        
        brand_text = tk.Frame(brand_row, bg=self.theme['bg_main'])
        brand_text.pack(side='left')
        
        txt_row = tk.Frame(brand_text, bg=self.theme['bg_main'])
        txt_row.pack(anchor='w')
        tk.Label(txt_row, text="Byte ", font=("Segoe UI", 28, "bold"), bg=self.theme['bg_main'], fg=self.theme['text_main']).pack(side='left')
        tk.Label(txt_row, text="& Brew", font=("Segoe UI", 28, "bold"), bg=self.theme['bg_main'], fg=self.theme['accent']).pack(side='left')

        tk.Label(brand_text, text="C O F F E E   •   C O D E   •   C R E A T E", font=("Segoe UI", 9, "bold"), 
                 bg=self.theme['bg_main'], fg=self.theme['text_muted']).pack(anchor='w')

        tk.Label(form_card, text="Welcome back", font=("Segoe UI", 22, "bold"), bg=self.theme['bg_main'], fg=self.theme['text_main']).pack(pady=(30, 5))
        tk.Label(form_card, text="Choose how you'd like to sign in to your POS.", font=("Segoe UI", 11), bg=self.theme['bg_main'], fg=self.theme['text_muted']).pack(pady=(0, 30))

        def create_role_button(parent, icon, title, subtitle, role_command):
            frame = tk.Frame(parent, bg=self.theme['bg_card'], highlightbackground=self.theme['border'], highlightthickness=1, cursor="hand2")
            frame.pack(fill='x', pady=10, ipady=8)

            inner = tk.Frame(frame, bg=self.theme['bg_card'], cursor="hand2")
            inner.pack(fill='x', padx=20, pady=12)

            icon_frame = tk.Frame(inner, bg=self.theme['bg_card'], width=45, height=45)
            icon_frame.pack(side='left', padx=(0, 20))
            icon_frame.pack_propagate(False)

            icon_lbl = tk.Label(icon_frame, text=icon, font=("Segoe UI Emoji", 24), bg=self.theme['bg_card'], fg=self.theme['text_muted'], cursor="hand2")
            icon_lbl.place(relx=0.5, rely=0.5, anchor="center")

            text_frame = tk.Frame(inner, bg=self.theme['bg_card'], cursor="hand2")
            text_frame.pack(side='left', fill='x', expand=True)
            
            title_lbl = tk.Label(text_frame, text=title, font=("Segoe UI", 13, "bold"), bg=self.theme['bg_card'], fg=self.theme['text_main'], cursor="hand2", anchor='w')
            title_lbl.pack(fill='x')
            
            sub_lbl = tk.Label(text_frame, text=subtitle, font=("Segoe UI", 10), bg=self.theme['bg_card'], fg=self.theme['text_muted'], cursor="hand2", anchor='w')
            sub_lbl.pack(fill='x')

            arrow_lbl = tk.Label(inner, text="›", font=("Segoe UI", 22), bg=self.theme['bg_card'], fg=self.theme['border'], cursor="hand2")
            arrow_lbl.pack(side='right')

            widgets = [frame, inner, icon_frame, icon_lbl, text_frame, title_lbl, sub_lbl, arrow_lbl]
            for w in widgets:
                w.bind("<Button-1>", lambda e: role_command())
                w.bind("<Enter>", lambda e: self.on_hover(widgets, True))
                w.bind("<Leave>", lambda e: self.on_hover(widgets, False))

        create_role_button(form_card, "🛡️", "Admin / Owner", "Menus, staff, reports and settings", lambda: self.open_login('admin'))
        create_role_button(form_card, "📄", "Cashier", "Take orders and process payments", lambda: self.open_login('cashier'))

        tk.Label(form_card, text="Need help? Contact your admin.", font=("Segoe UI", 10), bg=self.theme['bg_main'], fg=self.theme['text_muted']).pack(pady=(40, 0))

    def on_hover(self, widgets, is_hover):
        color = self.theme['bg_main'] if is_hover else self.theme['bg_card']
        for w in widgets:
            w.config(bg=color)

    def open_login(self, role):
        self.root.withdraw()
        LoginScreen(self, role, self.on_login_success)

    def on_login_success(self, user_data):
        self.theme = DARK_THEME if APP_SETTINGS['is_dark_mode'] else LIGHT_THEME
        
        for widget in self.root.winfo_children():
            widget.destroy()
            
        if user_data['role'] == 'admin':
            AdminDashboard(self.root, user_data, self.theme)
        elif user_data['role'] == 'cashier':
            CashierPOS(self.root, user_data, self.theme)

if __name__ == "__main__":
    root = tk.Tk()
    app = RoleSelectionApp(root)
    root.mainloop()