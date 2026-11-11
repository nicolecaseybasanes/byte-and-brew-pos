# admin/employees.py
import tkinter as tk
from tkinter import ttk, messagebox
from config.settings import LIGHT_THEME, DARK_THEME
from database.connection import get_db_connection
from utils.security import hash_password

# --- GLOBAL STATE ---
FORM_STATE = {
    'mode': 'create',
    'user_id': None,
    'name': '',
    'username': '',
    'pwd': '',
    'role': 'Cashier',
    'status': 'Active'
}

class EmployeeManager:
    def __init__(self, parent_frame, theme):
        self.parent = parent_frame
        self.theme = theme
        
        self.current_mode = FORM_STATE['mode']
        self.edit_user_id = FORM_STATE['user_id']
        
        self.ph_name = "Enter full name..."
        self.ph_user = "Enter a unique username..."
        self.ph_pwd = "••••••••"
        
        self.is_ph_name = not bool(FORM_STATE['name'])
        self.is_ph_user = not bool(FORM_STATE['username'])
        self.is_ph_pwd = not bool(FORM_STATE['pwd'])
        
        self.create_ui()
        self.load_data()
        self.restore_form_state()

    def create_ui(self):
        self.parent.configure(bg=self.theme['bg_main'])
        
        header_frame = tk.Frame(self.parent, bg=self.theme['bg_main'])
        header_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(header_frame, text="Employees", font=("Segoe UI", 22, "bold"),
                 bg=self.theme['bg_main'], fg=self.theme['text_main']).pack(anchor='w')
        tk.Label(header_frame, text="Manage staff access and create employee accounts.", font=("Segoe UI", 10),
                 bg=self.theme['bg_main'], fg=self.theme['text_muted']).pack(anchor='w', pady=(2, 0))

        # --- MAIN LAYOUT ---
        main_content = tk.Frame(self.parent, bg=self.theme['bg_main'])
        main_content.pack(fill='both', expand=True)

        # 1. RIGHT PANEL (Fixed width, packed first)
        right_panel = tk.Frame(main_content, bg=self.theme['bg_card'], width=360, highlightbackground=self.theme['border'], highlightthickness=1)
        right_panel.pack(side='right', fill='y', padx=(15, 0))
        right_panel.pack_propagate(False) 
        
        # 2. LEFT PANEL (Fills remaining space)
        left_panel = tk.Frame(main_content, bg=self.theme['bg_main'])
        left_panel.pack(side='left', fill='both', expand=True)

        # ==========================================
        # LEFT PANEL CONTENT (Cards & Table)
        # ==========================================
        cards_frame = tk.Frame(left_panel, bg=self.theme['bg_main'])
        cards_frame.pack(fill='x', pady=(0, 15))
        
        self.card_total = self.create_card(cards_frame, "Employee accounts", "0", "Cashier access only")
        self.card_active = self.create_card(cards_frame, "Active accounts", "0", "Inactive accounts")

        table_container = tk.Frame(left_panel, bg=self.theme['bg_card'], highlightbackground=self.theme['border'], highlightthickness=1)
        table_container.pack(fill='both', expand=True)

        table_header = tk.Frame(table_container, bg=self.theme['bg_card'])
        table_header.pack(fill='x', padx=15, pady=15)
        
        tk.Label(table_header, text="Employee accounts", font=("Segoe UI", 12, "bold"), bg=self.theme['bg_card'], fg=self.theme['text_main']).pack(anchor='w')
        tk.Label(table_header, text="Click a row to edit the employee account.", font=("Segoe UI", 9), bg=self.theme['bg_card'], fg=self.theme['text_muted']).pack(anchor='w', pady=(0, 10))

        search_frame = tk.Frame(table_header, bg=self.theme['bg_card'])
        search_frame.pack(fill='x', pady=(5, 0))
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=("Segoe UI", 10), 
                                     bg=self.theme['bg_main'], fg=self.theme['text_main'], relief="flat",
                                     highlightbackground=self.theme['border'], highlightthickness=1)
        self.search_entry.pack(side='left', fill='x', expand=True, ipady=5, padx=(0, 10))
        
        self.search_entry.insert(0, "Search name or username...")
        self.search_entry.config(fg=self.theme['text_muted'])
        self.search_entry.bind('<FocusIn>', self.on_search_in)
        self.search_entry.bind('<FocusOut>', self.on_search_out)
        self.search_entry.bind('<KeyRelease>', self.filter_table)

        self.status_filter = ttk.Combobox(search_frame, values=["All statuses", "Active", "Inactive"], 
                                          font=("Segoe UI", 9), state="readonly", width=15)
        self.status_filter.set("All statuses")
        self.status_filter.pack(side='right')
        self.status_filter.bind('<<ComboboxSelected>>', self.filter_table)

        tree_frame = tk.Frame(table_container, bg=self.theme['bg_card'])
        tree_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=self.theme['bg_card'], foreground=self.theme['text_main'], rowheight=35, fieldbackground=self.theme['bg_card'], font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background=self.theme['bg_main'], foreground=self.theme['text_muted'], font=("Segoe UI", 8, "bold"))
        style.map("Treeview", background=[('selected', self.theme['accent'])], foreground=[('selected', self.theme['accent_fg'])])

        columns = ("Employee", "Username", "Role", "Status")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor='w', minwidth=100)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        vsb.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=vsb.set)
        
        hsb = ttk.Scrollbar(table_container, orient="horizontal", command=self.tree.xview)
        hsb.pack(side='bottom', fill='x', padx=15)
        self.tree.configure(xscrollcommand=hsb.set)

        self.tree.pack(side='left', fill='both', expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

        # ==========================================
        # RIGHT PANEL CONTENT (Form)
        # ==========================================
        self.form_container = tk.Frame(right_panel, bg=self.theme['bg_card'])
        self.form_container.pack(fill='both', expand=True)
        self.build_form()

    def build_form(self):
        # Clear existing form
        for widget in self.form_container.winfo_children():
            widget.destroy()

        # FIXED: Reduced the outer padding from 20 to 10
        pad_frame = tk.Frame(self.form_container, bg=self.theme['bg_card'])
        pad_frame.pack(fill='both', expand=True, padx=15, pady=10)

        is_edit = (self.current_mode == 'edit')
        title_text = "Edit employee account" if is_edit else "Create employee account"
        sub_text = f"Editing: {FORM_STATE['name']}" if is_edit else "New account · all fields are required"

        # --- 1. PACK BUTTONS AT THE BOTTOM FIRST ---
        btn_frame = tk.Frame(pad_frame, bg=self.theme['bg_card'])
        # FIXED: Reduced bottom padding from 20 to 10
        btn_frame.pack(side='bottom', fill='x', pady=(10, 0))
        
        if is_edit:
            tk.Button(btn_frame, text="Cancel Edit", font=("Segoe UI", 10), bg=self.theme['btn_secondary'], fg=self.theme['btn_secondary_text'],
                      relief="flat", cursor="hand2", command=self.cancel_edit, pady=6).pack(fill='x', pady=(0, 5))
            tk.Button(btn_frame, text="Save Changes", font=("Segoe UI", 10, "bold"), bg=self.theme['accent'], fg=self.theme['accent_fg'],
                      activebackground=self.theme['accent_hover'], activeforeground=self.theme['accent_fg'],
                      relief="flat", cursor="hand2", command=self.save_edit, pady=6).pack(fill='x')
        else:
            tk.Button(btn_frame, text="Clear Form", font=("Segoe UI", 10), bg=self.theme['btn_secondary'], fg=self.theme['btn_secondary_text'],
                      relief="flat", cursor="hand2", command=self.clear_form, pady=6).pack(fill='x', pady=(0, 5))
            tk.Button(btn_frame, text="Create account", font=("Segoe UI", 10, "bold"), bg=self.theme['accent'], fg=self.theme['accent_fg'],
                      activebackground=self.theme['accent_hover'], activeforeground=self.theme['accent_fg'],
                      relief="flat", cursor="hand2", command=self.create_account, pady=6).pack(fill='x')

        # --- 2. PACK FORM FIELDS ABOVE THE BUTTONS ---
        tk.Label(pad_frame, text=title_text, font=("Segoe UI", 14, "bold"),
                 bg=self.theme['bg_card'], fg=self.theme['text_main']).pack(anchor='w', side='top')
        # FIXED: Reduced bottom padding from 15 to 10
        tk.Label(pad_frame, text=sub_text, font=("Segoe UI", 9),
                 bg=self.theme['bg_card'], fg=self.theme['text_muted']).pack(anchor='w', pady=(0, 10), side='top')

        def create_field(label_text):
            # FIXED: Reduced label padding from (10, 5) to (8, 2)
            tk.Label(pad_frame, text=label_text, font=("Segoe UI", 9, "bold"),
                     bg=self.theme['bg_card'], fg=self.theme['text_main']).pack(anchor='w', pady=(8, 2), side='top')
            frame = tk.Frame(pad_frame, bg=self.theme['bg_card'], highlightbackground=self.theme['border'], highlightthickness=1)
            frame.pack(fill='x', side='top')
            # FIXED: Reduced inner height padding from 6 to 4
            entry = tk.Entry(frame, font=("Segoe UI", 10), bg=self.theme['bg_main'], fg=self.theme['text_main'], relief="flat")
            entry.pack(fill='x', ipady=4)
            entry.bind('<KeyRelease>', self.sync_state)
            return entry

        self.name_entry = create_field("Employee name")
        self.user_entry = create_field("Username")
        
        # FIXED: Reduced combo box padding
        tk.Label(pad_frame, text="Role", font=("Segoe UI", 9, "bold"), bg=self.theme['bg_card'], fg=self.theme['text_main']).pack(anchor='w', pady=(8, 2), side='top')
        self.role_combo = ttk.Combobox(pad_frame, font=("Segoe UI", 10), values=["Cashier", "Admin"], state="readonly")
        self.role_combo.pack(fill='x', ipady=2, side='top')
        self.role_combo.bind('<<ComboboxSelected>>', self.sync_state)

        if is_edit:
            tk.Label(pad_frame, text="Account Status", font=("Segoe UI", 9, "bold"), bg=self.theme['bg_card'], fg=self.theme['text_main']).pack(anchor='w', pady=(8, 2), side='top')
            self.status_combo = ttk.Combobox(pad_frame, font=("Segoe UI", 10), values=["Active", "Inactive"], state="readonly")
            self.status_combo.pack(fill='x', ipady=2, side='top')
            self.status_combo.bind('<<ComboboxSelected>>', self.sync_state)

        pwd_label = "New Password (optional)" if is_edit else "Password"
        self.pwd_entry = create_field(pwd_label)
        self.pwd_entry.config(show="•")

    # --- STATE & PLACEHOLDER LOGIC ---
    def sync_state(self, event=None):
        FORM_STATE['name'] = self.name_entry.get() if not self.is_ph_name else ""
        FORM_STATE['username'] = self.user_entry.get() if not self.is_ph_user else ""
        FORM_STATE['pwd'] = self.pwd_entry.get() if not self.is_ph_pwd else ""
        FORM_STATE['role'] = self.role_combo.get()
        if self.current_mode == 'edit':
            FORM_STATE['status'] = self.status_combo.get()

    def restore_form_state(self):
        # Name
        if FORM_STATE['name']:
            self.name_entry.insert(0, FORM_STATE['name'])
            self.name_entry.config(fg=self.theme['text_main'])
            self.is_ph_name = False
        else:
            self.name_entry.insert(0, self.ph_name)
            self.name_entry.config(fg=self.theme['text_muted'])
            self.is_ph_name = True

        # Username
        if FORM_STATE['username']:
            self.user_entry.insert(0, FORM_STATE['username'])
            self.user_entry.config(fg=self.theme['text_main'])
            self.is_ph_user = False
        else:
            self.user_entry.insert(0, self.ph_user)
            self.user_entry.config(fg=self.theme['text_muted'])
            self.is_ph_user = True

        # Passwords
        if FORM_STATE['pwd']:
            self.pwd_entry.insert(0, FORM_STATE['pwd'])
            self.is_ph_pwd = False

        self.role_combo.set(FORM_STATE['role'])
        if self.current_mode == 'edit':
            self.status_combo.set(FORM_STATE['status'])

        # Attach placeholder bindings
        self.name_entry.bind('<FocusIn>', lambda e: self.on_focus_in(self.name_entry, self.ph_name, 'name'))
        self.name_entry.bind('<FocusOut>', lambda e: self.on_focus_out(self.name_entry, self.ph_name, 'name'))
        
        self.user_entry.bind('<FocusIn>', lambda e: self.on_focus_in(self.user_entry, self.ph_user, 'user'))
        self.user_entry.bind('<FocusOut>', lambda e: self.on_focus_out(self.user_entry, self.ph_user, 'user'))

        self.pwd_entry.bind('<FocusIn>', lambda e: self.on_focus_in(self.pwd_entry, self.ph_pwd, 'pwd', is_password=True))
        self.pwd_entry.bind('<FocusOut>', lambda e: self.on_focus_out(self.pwd_entry, self.ph_pwd, 'pwd', is_password=True))

    def on_focus_in(self, entry, placeholder, field, is_password=False):
        is_placeholder = getattr(self, f'is_ph_{field}')
        if is_placeholder:
            entry.delete(0, 'end')
            entry.config(fg=self.theme['text_main'])
            if is_password: entry.config(show="•")
            setattr(self, f'is_ph_{field}', False)

    def on_focus_out(self, entry, placeholder, field, is_password=False):
        if not entry.get():
            if is_password: entry.config(show="")
            entry.insert(0, placeholder)
            entry.config(fg=self.theme['text_muted'])
            setattr(self, f'is_ph_{field}', True)

    def cancel_edit(self):
        FORM_STATE.update({'mode': 'create', 'user_id': None, 'name': '', 'username': '', 'pwd': '', 'role': 'Cashier', 'status': 'Active'})
        self.current_mode = 'create'
        self.edit_user_id = None
        self.build_form()
        self.restore_form_state()
        self.tree.selection_remove(self.tree.selection())

    # --- ACTIONS ---
    def create_card(self, parent, title, value, subtitle):
        card = tk.Frame(parent, bg=self.theme['bg_card'], padx=20, pady=15, highlightbackground=self.theme['border'], highlightthickness=1)
        card.pack(side='left', fill='x', expand=True, padx=(0, 15))
        tk.Label(card, text=title, font=("Segoe UI", 9), bg=self.theme['bg_card'], fg=self.theme['text_muted']).pack(anchor='w')
        val_lbl = tk.Label(card, text=value, font=("Segoe UI", 22, "bold"), bg=self.theme['bg_card'], fg=self.theme['text_main'])
        val_lbl.pack(anchor='w', pady=(2, 2))
        tk.Label(card, text=subtitle, font=("Segoe UI", 8), bg=self.theme['bg_card'], fg=self.theme['text_muted']).pack(anchor='w')
        return val_lbl

    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT user_id, full_name, email, role, is_active FROM users ORDER BY user_id")
            users = cursor.fetchall()
            
            total_accounts = len(users)
            active_accounts = sum(1 for u in users if u[4] == True)
            
            self.card_total.config(text=str(total_accounts))
            self.card_active.config(text=str(active_accounts))

            for u in users:
                status = "Active" if u[4] else "Inactive"
                username = u[2].split('@')[0] if '@' in u[2] else u[2]
                self.tree.insert('', 'end', values=(u[1], username, u[3].capitalize(), status), tags=(str(u[0]),))
        except Exception as e:
            print(f"Error loading employees: {e}")
        finally:
            cursor.close()
            conn.close()

    def filter_table(self, event=None):
        search_term = self.search_entry.get().lower()
        if search_term == "search name or username...": search_term = ""
        status_filter = self.status_filter.get()
        
        for item in self.tree.get_children():
            values = self.tree.item(item, 'values')
            name, username, status = values[0].lower(), values[1].lower(), values[3]
            
            match_search = (search_term in name) or (search_term in username)
            match_status = (status_filter == "All statuses") or (status == status_filter)
            
            if match_search and match_status:
                self.tree.reattach(item, '', 'end')
            else:
                self.tree.detach(item)

    def on_row_select(self, event):
        selected = self.tree.selection()
        if not selected: return
        
        values = self.tree.item(selected[0], 'values')
        user_id = self.tree.item(selected[0], 'tags')[0]
        
        FORM_STATE['mode'] = 'edit'
        FORM_STATE['user_id'] = user_id
        FORM_STATE['name'] = values[0]
        FORM_STATE['username'] = values[1]
        FORM_STATE['role'] = values[2]
        FORM_STATE['status'] = values[3]
        FORM_STATE['pwd'] = ""
        
        self.current_mode = 'edit'
        self.edit_user_id = user_id
        
        self.build_form()
        self.restore_form_state()

    def save_edit(self):
        self.sync_state()
        
        name = FORM_STATE['name']
        username = FORM_STATE['username']
        role = FORM_STATE['role'].lower()
        status = FORM_STATE['status']
        pwd = FORM_STATE['pwd']
        user_id = FORM_STATE['user_id']

        if not name or not username:
            messagebox.showerror("Error", "Name and Username are required.", parent=self.parent)
            return
            
        if pwd:
            if len(pwd) < 6:
                messagebox.showerror("Error", "Password must be at least 6 characters.", parent=self.parent)
                return

        is_active = 1 if status == "Active" else 0
        email = f"{username}@byteandbrew.com"

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if pwd:
                hashed_pwd = hash_password(pwd)
                cursor.execute("UPDATE users SET full_name=?, email=?, role=?, is_active=?, password_hash=? WHERE user_id=?", 
                               (name, email, role, is_active, hashed_pwd, user_id))
            else:
                cursor.execute("UPDATE users SET full_name=?, email=?, role=?, is_active=? WHERE user_id=?", 
                               (name, email, role, is_active, user_id))
            
            conn.commit()
            self.load_data()
            self.cancel_edit() 
            messagebox.showinfo("Success", "Employee account updated.", parent=self.parent)
        except Exception as e:
            conn.rollback()
            if "UNIQUE" in str(e).upper() or "PRIMARY KEY" in str(e).upper():
                messagebox.showerror("Error", "This username is already taken.", parent=self.parent)
            else:
                messagebox.showerror("Database Error", str(e), parent=self.parent)
        finally:
            cursor.close()
            conn.close()

    def create_account(self):
        self.sync_state()

        name = FORM_STATE['name']
        username = FORM_STATE['username']
        pwd = FORM_STATE['pwd']
        role = FORM_STATE['role'].lower()

        if not name or not username or not pwd:
            messagebox.showerror("Error", "All fields are required.", parent=self.parent)
            return
            
        if len(pwd) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters.", parent=self.parent)
            return

        email = f"{username}@byteandbrew.com"
        hashed_pwd = hash_password(pwd)

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (full_name, email, password_hash, role) VALUES (?, ?, ?, ?)", 
                           (name, email, hashed_pwd, role))
            conn.commit()
            self.load_data()
            self.clear_form()
            messagebox.showinfo("Success", f"Account created for {name}.", parent=self.parent)
        except Exception as e:
            conn.rollback()
            if "UNIQUE" in str(e).upper() or "PRIMARY KEY" in str(e).upper():
                messagebox.showerror("Error", "This username is already taken.", parent=self.parent)
            else:
                messagebox.showerror("Database Error", str(e), parent=self.parent)
        finally:
            cursor.close()
            conn.close()

    def clear_form(self):
        FORM_STATE.update({'name': '', 'username': '', 'pwd': '', 'role': 'Cashier'})
        self.is_ph_name = True
        self.is_ph_user = True
        self.is_ph_pwd = True
        
        self.name_entry.delete(0, 'end')
        self.user_entry.delete(0, 'end')
        self.pwd_entry.delete(0, 'end')
        self.role_combo.set("Cashier")
        self.restore_form_state()

    def on_search_in(self, event):
        if self.search_entry.get() == "Search name or username...":
            self.search_entry.delete(0, 'end')
            self.search_entry.config(fg=self.theme['text_main'])
            
    def on_search_out(self, event):
        if not self.search_entry.get():
            self.search_entry.insert(0, "Search name or username...")
            self.search_entry.config(fg=self.theme['text_muted'])