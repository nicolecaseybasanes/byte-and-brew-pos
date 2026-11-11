# admin/products.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import shutil
from config.settings import LIGHT_THEME, DARK_THEME
from database.connection import get_db_connection

FORM_STATE = {
    'mode': 'add', 'product_id': None, 'name': '', 'category': '', 'price': '', 'availability': 'Active', 'image_path': ''
}

class ProductManager:
    def __init__(self, parent_frame, theme):
        self.parent = parent_frame
        self.theme = theme
        self.current_mode = FORM_STATE['mode']
        self.edit_product_id = FORM_STATE['product_id']
        
        self.ph_name = "Enter product name..."
        self.ph_price = "0.00"
        self.ph_search = "Search by product name..."
        
        self.create_ui()
        self.load_data()
        self.restore_form_state()

    def create_ui(self):
        self.parent.configure(bg=self.theme['bg_main'])
        
        header_frame = tk.Frame(self.parent, bg=self.theme['bg_main'])
        header_frame.pack(fill='x', pady=(0, 15))
        
        title_frame = tk.Frame(header_frame, bg=self.theme['bg_main'])
        title_frame.pack(side='left')
        tk.Label(title_frame, text="Products", font=("Segoe UI", 22, "bold"),
                 bg=self.theme['bg_main'], fg=self.theme['text_main']).pack(anchor='w')
        tk.Label(title_frame, text="Manage menu items, pricing and cashier availability.", font=("Segoe UI", 10),
                 bg=self.theme['bg_main'], fg=self.theme['text_muted']).pack(anchor='w', pady=(2, 0))

        tk.Button(header_frame, text="+ Add product", font=("Segoe UI", 10, "bold"), 
                  bg=self.theme['accent'], fg=self.theme['accent_fg'],
                  activebackground=self.theme['accent_hover'], activeforeground=self.theme['accent_fg'],
                  relief="flat", cursor="hand2", command=self.start_add_mode, padx=15, pady=8).pack(side='right', anchor='s')

        main_content = tk.Frame(self.parent, bg=self.theme['bg_main'])
        main_content.pack(fill='both', expand=True)

        # LEFT PANEL
        left_panel = tk.Frame(main_content, bg=self.theme['bg_main'])
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 15))

        cards_frame = tk.Frame(left_panel, bg=self.theme['bg_main'])
        cards_frame.pack(fill='x', pady=(0, 15))
        
        self.card_total = self.create_card(cards_frame, "Total products", "0", "Complete menu catalog")
        self.card_active = self.create_card(cards_frame, "Active products", "0", "Available in the cashier workspace")
        self.card_categories = self.create_card(cards_frame, "Categories in use", "0 of 0", "Side dishes has no products")

        filter_frame = tk.Frame(left_panel, bg=self.theme['bg_main'])
        filter_frame.pack(fill='x', pady=(0, 15))

        search_box = tk.Frame(filter_frame, bg=self.theme['bg_main'])
        search_box.pack(side='left', fill='x', expand=True, padx=(0, 10))
        tk.Label(search_box, text="Search products", font=("Segoe UI", 9, "bold"), bg=self.theme['bg_main'], fg=self.theme['text_main']).pack(anchor='w', pady=(0, 5))
        
        self.search_entry = tk.Entry(search_box, font=("Segoe UI", 10), bg=self.theme['bg_card'], fg=self.theme['text_muted'], 
                                     relief="flat", highlightbackground=self.theme['border'], highlightthickness=1)
        self.search_entry.pack(fill='x', ipady=5)
        self.search_entry.insert(0, self.ph_search)
        self.search_entry.bind('<FocusIn>', self.on_search_in)
        self.search_entry.bind('<FocusOut>', self.on_search_out)
        self.search_entry.bind('<KeyRelease>', self.filter_table)

        cat_filter_box = tk.Frame(filter_frame, bg=self.theme['bg_main'], width=150)
        cat_filter_box.pack(side='left', padx=(0, 10))
        cat_filter_box.pack_propagate(False)
        tk.Label(cat_filter_box, text="Category", font=("Segoe UI", 9, "bold"), bg=self.theme['bg_main'], fg=self.theme['text_main']).pack(anchor='w', pady=(0, 5))
        self.cat_filter = ttk.Combobox(cat_filter_box, font=("Segoe UI", 10), state="readonly")
        self.cat_filter.pack(fill='x', ipady=3)
        self.cat_filter.bind('<<ComboboxSelected>>', self.filter_table)

        avail_filter_box = tk.Frame(filter_frame, bg=self.theme['bg_main'], width=150)
        avail_filter_box.pack(side='left')
        avail_filter_box.pack_propagate(False)
        tk.Label(avail_filter_box, text="Availability", font=("Segoe UI", 9, "bold"), bg=self.theme['bg_main'], fg=self.theme['text_main']).pack(anchor='w', pady=(0, 5))
        self.avail_filter = ttk.Combobox(avail_filter_box, values=["All statuses", "Active", "Inactive"], font=("Segoe UI", 10), state="readonly")
        self.avail_filter.set("All statuses")
        self.avail_filter.pack(fill='x', ipady=3)
        self.avail_filter.bind('<<ComboboxSelected>>', self.filter_table)

        table_container = tk.Frame(left_panel, bg=self.theme['bg_card'], highlightbackground=self.theme['border'], highlightthickness=1)
        table_container.pack(fill='both', expand=True)

        table_header = tk.Frame(table_container, bg=self.theme['bg_card'])
        table_header.pack(fill='x', padx=15, pady=15)
        tk.Label(table_header, text="Product catalog", font=("Segoe UI", 12, "bold"), bg=self.theme['bg_card'], fg=self.theme['text_main']).pack(anchor='w')
        self.table_subtitle = tk.Label(table_header, text="0 products · select Edit to update an item", font=("Segoe UI", 9), bg=self.theme['bg_card'], fg=self.theme['text_muted'])
        self.table_subtitle.pack(anchor='w', pady=(2, 0))

        tree_frame = tk.Frame(table_container, bg=self.theme['bg_card'])
        tree_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=self.theme['bg_card'], foreground=self.theme['text_main'], rowheight=35, fieldbackground=self.theme['bg_card'], font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background=self.theme['bg_main'], foreground=self.theme['text_muted'], font=("Segoe UI", 8, "bold"))
        style.map("Treeview", background=[('selected', self.theme['border'])], foreground=[('selected', self.theme['text_main'])])

        columns = ("Product", "Category", "Price", "Status", "Action")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.tree.heading(col, text=col.upper())
            self.tree.column(col, anchor='w')
        
        self.tree.column("Price", width=80)
        self.tree.column("Action", width=50)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        vsb.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=vsb.set)
        
        hsb = ttk.Scrollbar(table_container, orient="horizontal", command=self.tree.xview)
        hsb.pack(side='bottom', fill='x', padx=15)
        self.tree.configure(xscrollcommand=hsb.set)

        self.tree.pack(side='left', fill='both', expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

        self.footer_label = tk.Label(table_container, text="Showing 0 of 0 products", font=("Segoe UI", 9), bg=self.theme['bg_card'], fg=self.theme['text_muted'])
        self.footer_label.pack(anchor='w', padx=15, pady=(0, 15))

        # RIGHT PANEL
        right_panel = tk.Frame(main_content, bg=self.theme['bg_card'], width=360, highlightbackground=self.theme['border'], highlightthickness=1)
        right_panel.pack(side='right', fill='y')
        right_panel.pack_propagate(False) 
        
        self.form_container = tk.Frame(right_panel, bg=self.theme['bg_card'])
        self.form_container.pack(fill='both', expand=True)
        self.build_form()

    def build_form(self):
        for widget in self.form_container.winfo_children():
            widget.destroy()

        pad_frame = tk.Frame(self.form_container, bg=self.theme['bg_card'])
        pad_frame.pack(fill='both', expand=True, padx=20, pady=20)

        is_edit = (self.current_mode == 'edit')
        title_text = "Edit product" if is_edit else "Add product"
        sub_text = f"Selected · {FORM_STATE['name']}" if is_edit else "New item · all fields are required"

        btn_frame = tk.Frame(pad_frame, bg=self.theme['bg_card'])
        btn_frame.pack(side='bottom', fill='x', pady=(20, 0))
        
        tk.Button(btn_frame, text="Cancel", font=("Segoe UI", 10), bg=self.theme['btn_secondary'], fg=self.theme['btn_secondary_text'],
                  relief="flat", cursor="hand2", command=self.cancel_edit, pady=8).pack(side='left', fill='x', expand=True, padx=(0, 5))
                  
        tk.Button(btn_frame, text="Save changes" if is_edit else "Create product", font=("Segoe UI", 10, "bold"), bg=self.theme['accent'], fg=self.theme['accent_fg'],
                  activebackground=self.theme['accent_hover'], activeforeground=self.theme['accent_fg'],
                  relief="flat", cursor="hand2", command=self.save_product, pady=8).pack(side='right', fill='x', expand=True, padx=(5, 0))

        tk.Label(pad_frame, text=title_text, font=("Segoe UI", 14, "bold"),
                 bg=self.theme['bg_card'], fg=self.theme['text_main']).pack(anchor='w', side='top')
        tk.Label(pad_frame, text=sub_text, font=("Segoe UI", 9),
                 bg=self.theme['bg_card'], fg=self.theme['text_muted']).pack(anchor='w', pady=(0, 15), side='top')

        def create_field(label_text, is_entry=True):
            tk.Label(pad_frame, text=label_text, font=("Segoe UI", 9, "bold"),
                     bg=self.theme['bg_card'], fg=self.theme['text_main']).pack(anchor='w', pady=(10, 5), side='top')
            frame = tk.Frame(pad_frame, bg=self.theme['bg_card'], highlightbackground=self.theme['border'], highlightthickness=1)
            frame.pack(fill='x', side='top')
            
            if is_entry:
                entry = tk.Entry(frame, font=("Segoe UI", 10), bg=self.theme['bg_main'], fg=self.theme['text_main'], relief="flat")
                entry.pack(fill='x', ipady=6)
                entry.bind('<KeyRelease>', self.sync_state)
                return entry
            else:
                combo = ttk.Combobox(frame, font=("Segoe UI", 10), state="readonly")
                combo.pack(fill='x', ipady=3)
                combo.bind('<<ComboboxSelected>>', self.sync_state)
                return combo

        self.name_entry = create_field("Product name")
        self.cat_combo = create_field("Category", is_entry=False)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT category_name FROM categories WHERE is_active = 1")
            cats = [r[0] for r in cursor.fetchall()]
            cursor.close()
            conn.close()
            self.cat_combo['values'] = cats
        except Exception:
            pass

        self.price_entry = create_field("Price (₱)")
        self.avail_combo = create_field("Availability", is_entry=False)
        self.avail_combo['values'] = ["Active", "Inactive"]

        # --- IMAGE SECTION FIX ---
        tk.Label(pad_frame, text="Product Image", font=("Segoe UI", 9, "bold"),
                 bg=self.theme['bg_card'], fg=self.theme['text_main']).pack(anchor='w', pady=(10, 5), side='top')
        
        img_frame = tk.Frame(pad_frame, bg=self.theme['bg_card'])
        img_frame.pack(fill='x', side='top')
        
        def browse_image():
            filepath = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.jpeg *.png")])
            if filepath:
                filename = os.path.basename(filepath)
                self.img_var.set(filename)
                self.sync_state()

        # 1. Pack the Button FIRST to the right. 
        # This guarantees it gets the space it needs before the Entry expands.
        browse_btn = tk.Button(img_frame, text="Browse", font=("Segoe UI", 9), bg=self.theme['btn_secondary'], fg=self.theme['btn_secondary_text'],
                               command=browse_image, padx=10)
        browse_btn.pack(side='right', padx=(5, 0), fill='y') 

        # 2. Pack the Entry to the left. It will fill the remaining space.
        self.img_var = tk.StringVar(value=FORM_STATE['image_path'])
        img_entry = tk.Entry(img_frame, textvariable=self.img_var, font=("Segoe UI", 10), state='readonly', bg=self.theme['bg_main'], fg=self.theme['text_muted'])
        img_entry.pack(side='left', fill='x', expand=True, ipady=6)

    def sync_state(self, event=None):
        FORM_STATE['name'] = self.name_entry.get() if self.name_entry.get() != self.ph_name else ""
        FORM_STATE['category'] = self.cat_combo.get()
        FORM_STATE['price'] = self.price_entry.get() if self.price_entry.get() != self.ph_price else ""
        FORM_STATE['availability'] = self.avail_combo.get()
        FORM_STATE['image_path'] = self.img_var.get()

    def restore_form_state(self):
        if FORM_STATE['name']:
            self.name_entry.insert(0, FORM_STATE['name'])
            self.name_entry.config(fg=self.theme['text_main'])
        else:
            self.name_entry.insert(0, self.ph_name)
            self.name_entry.config(fg=self.theme['text_muted'])

        if FORM_STATE['category']:
            self.cat_combo.set(FORM_STATE['category'])
        elif self.cat_combo['values']:
            self.cat_combo.set(self.cat_combo['values'][0])

        if FORM_STATE['price']:
            self.price_entry.insert(0, FORM_STATE['price'])
            self.price_entry.config(fg=self.theme['text_main'])
        else:
            self.price_entry.insert(0, self.ph_price)
            self.price_entry.config(fg=self.theme['text_muted'])

        self.avail_combo.set(FORM_STATE['availability'])

        self.name_entry.bind('<FocusIn>', lambda e: self.on_focus_in(self.name_entry, self.ph_name))
        self.name_entry.bind('<FocusOut>', lambda e: self.on_focus_out(self.name_entry, self.ph_name))
        self.price_entry.bind('<FocusIn>', lambda e: self.on_focus_in(self.price_entry, self.ph_price))
        self.price_entry.bind('<FocusOut>', lambda e: self.on_focus_out(self.price_entry, self.ph_price))

    def on_focus_in(self, entry, placeholder):
        if entry.get() == placeholder:
            entry.delete(0, 'end')
            entry.config(fg=self.theme['text_main'])

    def on_focus_out(self, entry, placeholder):
        if not entry.get():
            entry.insert(0, placeholder)
            entry.config(fg=self.theme['text_muted'])

    def start_add_mode(self):
        FORM_STATE.update({'mode': 'add', 'product_id': None, 'name': '', 'category': '', 'price': '', 'availability': 'Active', 'image_path': ''})
        self.current_mode = 'add'
        self.edit_product_id = None
        self.build_form()
        self.restore_form_state()
        self.tree.selection_remove(self.tree.selection())

    def cancel_edit(self):
        self.start_add_mode()

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
            try:
                cursor.execute("SELECT p.product_id, p.product_name, c.category_name, p.price, p.is_available, p.image_path FROM products p LEFT JOIN categories c ON p.category_id = c.category_id ORDER BY p.product_name")
            except Exception:
                cursor.execute("SELECT p.product_id, p.product_name, c.category_name, p.price, p.is_available, NULL FROM products p LEFT JOIN categories c ON p.category_id = c.category_id ORDER BY p.product_name")
            products = cursor.fetchall()
            
            cursor.execute("SELECT COUNT(*) FROM products")
            total_prod = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM products WHERE is_available = 1")
            active_prod = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT category_id) FROM products")
            cats_in_use = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM categories")
            total_cats = cursor.fetchone()[0]

            self.card_total.config(text=str(total_prod))
            self.card_active.config(text=str(active_prod))
            self.card_categories.config(text=f"{cats_in_use} of {total_cats}")

            for p in products:
                status = "Active" if p[4] else "Inactive"
                self.tree.insert('', 'end', values=(p[1], p[2] or "N/A", f"₱{p[3]:.2f}", status, "Edit"), tags=(str(p[0]),))
            
            self.update_footer()
            self.update_category_filter()
            
        except Exception as e:
            print(f"Error loading products: {e}")
        finally:
            cursor.close()
            conn.close()

    def update_category_filter(self):
        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor()
        cursor.execute("SELECT category_name FROM categories WHERE is_active = 1")
        cats = ["All categories"] + [r[0] for r in cursor.fetchall()]
        cursor.close()
        conn.close()
        self.cat_filter['values'] = cats
        if not self.cat_filter.get():
            self.cat_filter.set("All categories")

    def update_footer(self):
        total_rows = len(self.tree.get_children(''))
        visible_rows = len(self.tree.get_children())
        self.footer_label.config(text=f"Showing {visible_rows} of {total_rows} products")
        self.table_subtitle.config(text=f"{total_rows} products · select Edit to update an item")

    def filter_table(self, event=None):
        search_term = self.search_entry.get().lower()
        if search_term == self.ph_search: search_term = ""
        cat_filter = self.cat_filter.get()
        avail_filter = self.avail_filter.get()
        
        for item in self.tree.get_children():
            values = self.tree.item(item, 'values')
            name, category, status = values[0].lower(), values[1], values[3]
            match_search = (search_term in name)
            match_cat = (cat_filter == "All categories") or (category == cat_filter)
            match_avail = (avail_filter == "All statuses") or (status == avail_filter)
            
            if match_search and match_cat and match_avail:
                self.tree.reattach(item, '', 'end')
            else:
                self.tree.detach(item)
        
        self.update_footer()

    def on_row_select(self, event):
        selected = self.tree.selection()
        if not selected: return
        values = self.tree.item(selected[0], 'values')
        product_id = self.tree.item(selected[0], 'tags')[0]
        
        FORM_STATE['mode'] = 'edit'
        FORM_STATE['product_id'] = product_id
        FORM_STATE['name'] = values[0]
        FORM_STATE['category'] = values[1]
        FORM_STATE['price'] = values[2].replace('₱', '')
        FORM_STATE['availability'] = values[3]
        
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT image_path FROM products WHERE product_id = ?", (product_id,))
            row = cursor.fetchone()
            if row: FORM_STATE['image_path'] = row[0] or ""
        except Exception:
            FORM_STATE['image_path'] = ""
        finally:
            cursor.close()
            conn.close()

        self.current_mode = 'edit'
        self.edit_product_id = product_id
        self.build_form()
        self.restore_form_state()

    def save_product(self):
        self.sync_state()
        name = FORM_STATE['name']
        category = FORM_STATE['category']
        price_str = FORM_STATE['price']
        availability = FORM_STATE['availability']
        image_path = FORM_STATE['image_path']
        product_id = FORM_STATE['product_id']

        if not name or not category or not price_str:
            messagebox.showerror("Error", "Name, Category, and Price are required.", parent=self.parent)
            return
        try:
            price = float(price_str)
        except ValueError:
            messagebox.showerror("Error", "Price must be a valid number.", parent=self.parent)
            return

        is_available = 1 if availability == "Active" else 0
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT category_id FROM categories WHERE category_name = ?", (category,))
            cat_row = cursor.fetchone()
            if not cat_row:
                messagebox.showerror("Error", "Invalid category selected.", parent=self.parent)
                return
            cat_id = cat_row[0]

            if self.current_mode == 'edit':
                try:
                    cursor.execute("UPDATE products SET product_name=?, category_id=?, price=?, is_available=?, image_path=? WHERE product_id=?", (name, cat_id, price, is_available, image_path, product_id))
                except Exception:
                    cursor.execute("UPDATE products SET product_name=?, category_id=?, price=?, is_available=? WHERE product_id=?", (name, cat_id, price, is_available, product_id))
            else:
                try:
                    cursor.execute("INSERT INTO products (product_name, category_id, price, is_available, image_path) VALUES (?, ?, ?, ?, ?)", (name, cat_id, price, is_available, image_path))
                except Exception:
                    cursor.execute("INSERT INTO products (product_name, category_id, price, is_available) VALUES (?, ?, ?, ?)", (name, cat_id, price, is_available))
            
            conn.commit()
            self.load_data()
            self.start_add_mode() 
            messagebox.showinfo("Success", "Product saved successfully.", parent=self.parent)
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Database Error", str(e), parent=self.parent)
        finally:
            cursor.close()
            conn.close()

    def on_search_in(self, event):
        if self.search_entry.get() == self.ph_search:
            self.search_entry.delete(0, 'end')
            self.search_entry.config(fg=self.theme['text_main'])
            
    def on_search_out(self, event):
        if not self.search_entry.get():
            self.search_entry.insert(0, self.ph_search)
            self.search_entry.config(fg=self.theme['text_muted'])