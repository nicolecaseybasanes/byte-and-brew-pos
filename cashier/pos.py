# cashier/pos.py
import tkinter as tk
from tkinter import ttk, messagebox
import os
from PIL import Image, ImageTk, ImageOps
from config.settings import LIGHT_THEME, DARK_THEME, APP_NAME, APP_SETTINGS, save_theme_pref
from database.connection import get_db_connection
from cashier.payment import PaymentWindow

class ScrollableFrame(tk.Frame):
    def __init__(self, container, bg_color, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = tk.Canvas(self, bg=bg_color, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=bg_color)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")


class CashierPOS:
    def __init__(self, root, user_data, theme):
        self.root = root
        self.user_data = user_data
        self.is_dark_mode = (theme == DARK_THEME)
        self.theme = theme
        
        self.root.deiconify() 
        self.root.title(f"Cashier POS - {APP_NAME}")
        self.root.geometry("1300x850") 
        self.root.eval('tk::PlaceWindow . center')

        for widget in self.root.winfo_children():
            widget.destroy()

        self.cart = {}
        self.current_category = None
        self.cat_buttons = {}
        
        self.search_placeholder = "Type a product name..."
        self.search_is_placeholder = True
        self.search_var = tk.StringVar()
        
        self.order_type_var = tk.StringVar(value="Dine In")

        self.build_ui()

    def toggle_theme(self):
        APP_SETTINGS['is_dark_mode'] = not APP_SETTINGS['is_dark_mode']
        save_theme_pref(APP_SETTINGS['is_dark_mode'])
        
        self.is_dark_mode = APP_SETTINGS['is_dark_mode']
        self.theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
        
        for widget in self.root.winfo_children():
            widget.destroy()
        self.build_ui()

    def build_ui(self):
        self.root.configure(bg=self.theme['bg_main'])

        header = tk.Frame(self.root, bg=self.theme['bg_card'], height=80, highlightbackground=self.theme['border'], highlightthickness=1)
        header.pack(fill='x')
        header.pack_propagate(False)

        logo_frame = tk.Frame(header, bg=self.theme['bg_card'])
        logo_frame.pack(side='left', padx=30, pady=20)
        
        tk.Label(logo_frame, text="BYTE AND BREW", font=("Segoe UI", 18, "bold"),
                 bg=self.theme['bg_card'], fg=self.theme['text_main']).pack(side='left')
                 
        tk.Label(logo_frame, text=" Point of Sale ", font=("Segoe UI", 9, "bold"),
                 bg=self.theme['badge_bg'], fg=self.theme['badge_fg']).pack(side='left', padx=15)

        moon_icon = "☀" if self.is_dark_mode else "☾"
        tk.Button(logo_frame, text=moon_icon, font=("Segoe UI", 18), bg=self.theme['bg_card'], fg=self.theme['text_main'],
                  relief="flat", cursor="hand2", command=self.toggle_theme).pack(side='left')

        tk.Button(header, text="Logout", font=("Segoe UI", 10), bg=self.theme['bg_card'], fg=self.theme['text_muted'],
                  relief="flat", cursor="hand2", command=self.root.destroy).pack(side='right', padx=20)

        tk.Label(header, text=f"Cashier: {self.user_data['full_name']}", font=("Segoe UI", 11, "bold"),
                 bg=self.theme['bg_card'], fg=self.theme['text_main']).pack(side='right', padx=15)

        main_container = tk.Frame(self.root, bg=self.theme['bg_main'])
        main_container.pack(fill='both', expand=True, padx=20, pady=20)

        # LEFT: MENU AREA
        left_panel = tk.Frame(main_container, bg=self.theme['bg_main'])
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 20))

        tk.Label(left_panel, text="Search products", font=("Segoe UI", 10, "bold"),
                 bg=self.theme['bg_main'], fg=self.theme['text_main']).pack(anchor='w', pady=(0, 5))

        search_container = tk.Frame(left_panel, bg=self.theme['bg_card'], highlightbackground=self.theme['border'], highlightthickness=1)
        search_container.pack(fill='x', pady=(0, 20))
        
        tk.Label(search_container, text="🔍", font=("Segoe UI", 12), bg=self.theme['bg_card'], fg=self.theme['text_muted']).pack(side='left', padx=(15, 5))
        
        self.search_entry = tk.Entry(search_container, textvariable=self.search_var, font=("Segoe UI", 11), 
                                     bg=self.theme['bg_card'], fg=self.theme['text_muted'], relief="flat")
        self.search_entry.pack(side='left', fill='x', expand=True, ipady=12)
        
        self.search_entry.insert(0, self.search_placeholder)
        self.search_entry.bind('<FocusIn>', self.on_search_focus_in)
        self.search_entry.bind('<FocusOut>', self.on_search_focus_out)
        self.search_entry.bind('<KeyRelease>', self.filter_products)
        
        tk.Label(search_container, text="Search all categories", font=("Segoe UI", 9), 
                 bg=self.theme['bg_card'], fg=self.theme['text_muted']).pack(side='right', padx=15)

        tk.Label(left_panel, text="Categories", font=("Segoe UI", 10, "bold"),
                 bg=self.theme['bg_main'], fg=self.theme['text_main']).pack(anchor='w', pady=(0, 5))

        self.cat_frame = tk.Frame(left_panel, bg=self.theme['bg_main'])
        self.cat_frame.pack(fill='x', pady=(0, 20))
        self.load_categories()

        product_header = tk.Frame(left_panel, bg=self.theme['bg_main'])
        product_header.pack(fill='x', pady=(10, 10))
        
        tk.Label(product_header, text="All products", font=("Segoe UI", 12, "bold"),
                 bg=self.theme['bg_main'], fg=self.theme['text_main']).pack(side='left')
                 
        self.product_count_label = tk.Label(product_header, text="0 products", font=("Segoe UI", 10),
                                            bg=self.theme['bg_main'], fg=self.theme['text_muted'])
        self.product_count_label.pack(side='right')

        self.product_scroll = ScrollableFrame(left_panel, bg_color=self.theme['bg_main'])
        self.product_scroll.pack(fill='both', expand=True)
        self.product_frame = self.product_scroll.scrollable_frame
        self.load_products()

        # RIGHT: CART AREA
        right_panel = tk.Frame(main_container, bg=self.theme['cart_bg'], width=450, highlightbackground=self.theme['border'], highlightthickness=1)
        right_panel.pack(side='right', fill='y')
        right_panel.pack_propagate(False)

        cart_header = tk.Frame(right_panel, bg=self.theme['cart_bg'])
        cart_header.pack(side='top', fill='x', padx=20, pady=(20, 0))
        
        title_row = tk.Frame(cart_header, bg=self.theme['cart_bg'])
        title_row.pack(fill='x')
        tk.Label(title_row, text="Current order", font=("Segoe UI", 16, "bold"), bg=self.theme['cart_bg'], fg=self.theme['text_main']).pack(side='left')
        
        status_badge = tk.Label(title_row, text="IN PROGRESS", font=("Segoe UI", 7, "bold"), bg=self.theme['badge_bg'], fg=self.theme['badge_fg'], padx=8, pady=3)
        status_badge.pack(side='right', pady=5)
        
        self.cart_summary_label = tk.Label(cart_header, text="New sale", font=("Segoe UI", 10), bg=self.theme['cart_bg'], fg=self.theme['text_muted'])
        self.cart_summary_label.pack(anchor='w', pady=(4, 15))
        
        tk.Frame(cart_header, height=1, bg=self.theme['divider']).pack(fill='x')

        # ORDER TYPE
        order_type_frame = tk.Frame(right_panel, bg=self.theme['cart_bg'])
        order_type_frame.pack(fill='x', padx=20, pady=(15, 0))
        
        tk.Label(order_type_frame, text="Order Type", font=("Segoe UI", 9, "bold"), bg=self.theme['cart_bg'], fg=self.theme['text_main']).pack(anchor='w', pady=(0,5))
        
        toggle_frame = tk.Frame(order_type_frame, bg=self.theme['cart_bg'])
        toggle_frame.pack(fill='x')
        
        self.dine_in_btn = tk.Button(toggle_frame, text="Dine In", font=("Segoe UI", 10, "bold"), 
                                     bg=self.theme['accent'], fg=self.theme['accent_fg'], 
                                     relief="flat", cursor="hand2", command=lambda: self.set_order_type("Dine In"))
        self.dine_in_btn.pack(side='left', fill='x', expand=True, padx=(0, 5), ipady=5)
        
        self.take_out_btn = tk.Button(toggle_frame, text="Take Out", font=("Segoe UI", 10), 
                                      bg=self.theme['btn_secondary'], fg=self.theme['btn_secondary_text'], 
                                      relief="flat", cursor="hand2", command=lambda: self.set_order_type("Take Out"))
        self.take_out_btn.pack(side='right', fill='x', expand=True, padx=(5, 0), ipady=5)
        
        tk.Frame(right_panel, height=10, bg=self.theme['cart_bg']).pack(fill='x')

        footer_frame = tk.Frame(right_panel, bg=self.theme['cart_bg'])
        footer_frame.pack(side='bottom', fill='x', padx=20, pady=(0, 20))

        tk.Frame(footer_frame, height=1, bg=self.theme['divider']).pack(fill='x', pady=(0, 15))

        self.subtotal_row = tk.Frame(footer_frame, bg=self.theme['cart_bg'])
        self.subtotal_row.pack(fill='x', pady=5)
        self.subtotal_label_left = tk.Label(self.subtotal_row, text="Subtotal • 0 items", font=("Segoe UI", 10), bg=self.theme['cart_bg'], fg=self.theme['text_muted'])
        self.subtotal_label_left.pack(side='left')
        self.subtotal_label_right = tk.Label(self.subtotal_row, text="₱0.00", font=("Segoe UI", 10, "bold"), bg=self.theme['cart_bg'], fg=self.theme['text_main'])
        self.subtotal_label_right.pack(side='right')

        total_row = tk.Frame(footer_frame, bg=self.theme['cart_bg'])
        total_row.pack(fill='x', pady=(5, 15))
        tk.Label(total_row, text="Total", font=("Segoe UI", 16, "bold"), bg=self.theme['cart_bg'], fg=self.theme['text_main']).pack(side='left')
        self.total_label = tk.Label(total_row, text="₱0.00", font=("Segoe UI", 24, "bold"), bg=self.theme['cart_bg'], fg=self.theme['text_main'])
        self.total_label.pack(side='right')

        self.pay_btn_frame = tk.Frame(footer_frame, bg=self.theme['accent'], cursor="hand2")
        self.pay_btn_frame.pack(fill='x', pady=(0, 15))
        
        self.pay_btn_left = tk.Label(self.pay_btn_frame, text="Take payment", font=("Segoe UI", 11, "bold"), bg=self.theme['accent'], fg=self.theme['accent_fg'], cursor="hand2", pady=12, padx=15)
        self.pay_btn_left.pack(side='left')
        
        self.pay_btn_right = tk.Label(self.pay_btn_frame, text="₱0.00 ➔", font=("Segoe UI", 11, "bold"), bg=self.theme['accent'], fg=self.theme['accent_fg'], cursor="hand2", pady=12, padx=15)
        self.pay_btn_right.pack(side='right')

        for widget in [self.pay_btn_frame, self.pay_btn_left, self.pay_btn_right]:
            widget.bind("<Button-1>", lambda e: self.open_payment())
            widget.bind("<Enter>", lambda e: self.on_pay_hover(True))
            widget.bind("<Leave>", lambda e: self.on_pay_hover(False))

        self.clear_btn = tk.Label(footer_frame, text="Clear order", font=("Segoe UI", 9), 
                              bg=self.theme['cart_bg'], fg=self.theme['text_muted'], cursor="hand2")
        self.clear_btn.pack(pady=(0, 5))
        self.clear_btn.bind("<Button-1>", lambda e: self.clear_cart())

        self.instruction_label = tk.Label(right_panel, text="Use − / + or type a quantity to update the order.", 
                                          font=("Segoe UI", 9), bg=self.theme['cart_bg'], fg=self.theme['text_muted'],
                                          wraplength=400, justify='center')
        self.instruction_label.pack(side='bottom', fill='x', padx=20, pady=(0, 10))

        self.cart_scroll = ScrollableFrame(right_panel, bg_color=self.theme['cart_bg'])
        self.cart_scroll.pack(side='top', fill='both', expand=True, padx=10)
        self.cart_display = self.cart_scroll.scrollable_frame

        self.update_cart_display()

    def set_order_type(self, order_type):
        self.order_type_var.set(order_type)
        if order_type == "Dine In":
            self.dine_in_btn.config(bg=self.theme['accent'], fg=self.theme['accent_fg'], font=("Segoe UI", 10, "bold"))
            self.take_out_btn.config(bg=self.theme['btn_secondary'], fg=self.theme['btn_secondary_text'], font=("Segoe UI", 10))
        else:
            self.take_out_btn.config(bg=self.theme['accent'], fg=self.theme['accent_fg'], font=("Segoe UI", 10, "bold"))
            self.dine_in_btn.config(bg=self.theme['btn_secondary'], fg=self.theme['btn_secondary_text'], font=("Segoe UI", 10))

    def on_search_focus_in(self, event):
        if self.search_is_placeholder:
            self.search_entry.delete(0, 'end')
            self.search_entry.config(fg=self.theme['text_main'])
            self.search_is_placeholder = False

    def on_search_focus_out(self, event):
        if not self.search_entry.get():
            self.search_entry.insert(0, self.search_placeholder)
            self.search_entry.config(fg=self.theme['text_muted'])
            self.search_is_placeholder = True

    def on_pay_hover(self, is_hover):
        color = self.theme['accent_hover'] if is_hover else self.theme['accent']
        self.pay_btn_frame.config(bg=color)
        self.pay_btn_left.config(bg=color)
        self.pay_btn_right.config(bg=color)

    def load_categories(self):
        for widget in self.cat_frame.winfo_children():
            widget.destroy()

        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor()
        cursor.execute("SELECT category_id, category_name FROM categories WHERE is_active = 1")
        categories = cursor.fetchall()
        cursor.close()
        conn.close()

        self.cat_buttons = {}
        
        def create_pill(text, cat_id):
            is_active = (cat_id == self.current_category)
            bg = self.theme['pill_active_bg'] if is_active else self.theme['pill_inactive_bg']
            fg = self.theme['pill_active_fg'] if is_active else self.theme['pill_inactive_fg']
            border = self.theme['pill_active_bg'] if is_active else self.theme['border']
            
            display_text = text if text == "All" else text.title()

            btn = tk.Button(self.cat_frame, text=display_text, font=("Segoe UI", 9, "bold" if is_active else "normal"), 
                            bg=bg, fg=fg, relief="flat", padx=15, pady=6, cursor="hand2",
                            highlightbackground=border, highlightthickness=1,
                            command=lambda: self.filter_by_category(cat_id, btn))
            btn.pack(side='left', padx=(0, 10))
            self.cat_buttons[cat_id] = btn

        create_pill("All", None)
        for cat in categories:
            create_pill(cat[1], cat[0])

    def update_active_pill(self, category_id):
        for cid, b in self.cat_buttons.items():
            if cid == category_id:
                b.config(bg=self.theme['pill_active_bg'], fg=self.theme['pill_active_fg'], 
                         font=("Segoe UI", 9, "bold"), highlightbackground=self.theme['pill_active_bg'])
            else:
                b.config(bg=self.theme['pill_inactive_bg'], fg=self.theme['pill_inactive_fg'], 
                         font=("Segoe UI", 9), highlightbackground=self.theme['border'])

    def filter_by_category(self, category_id, btn):
        self.current_category = category_id
        self.update_active_pill(category_id)
        self.load_products(self.search_entry.get().strip())

    def filter_products(self, event=None):
        search_term = "" if self.search_is_placeholder else self.search_entry.get().strip()
        
        if search_term:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT category_id 
                    FROM products 
                    WHERE product_name LIKE ? AND is_available = 1
                """, (f"%{search_term}%",))
                categories = cursor.fetchall()
                cursor.close()
                conn.close()
                
                if len(categories) == 1 and categories[0][0] is not None:
                    new_cat_id = categories[0][0]
                    self.current_category = new_cat_id
                    self.update_active_pill(new_cat_id)
                elif len(categories) > 1:
                    self.current_category = None
                    self.update_active_pill(None)
        else:
            self.current_category = None
            self.update_active_pill(None)

        self.load_products(search_term)

    def load_products(self, search_term=None):
        for widget in self.product_frame.winfo_children():
            widget.destroy()

        if search_term is None:
            search_term = "" if self.search_is_placeholder else self.search_entry.get().strip()

        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor()
        
        query = """
            SELECT p.product_id, p.product_name, p.price, p.image_path 
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.category_id
            WHERE p.is_available = 1 
              AND (c.is_active = 1 OR p.category_id IS NULL)
        """
        params = []
        
        if self.current_category:
            query += " AND p.category_id = ?"
            params.append(self.current_category)
        if search_term:
            query += " AND p.product_name LIKE ?"
            params.append(f"%{search_term}%")

        cursor.execute(query, params)
        products = cursor.fetchall()
        cursor.close()
        conn.close()

        self.product_count_label.config(text=f"{len(products)} products")

        row, col = 0, 0
        for prod in products:
            card = tk.Frame(self.product_frame, bg=self.theme['bg_card'], highlightbackground=self.theme['border'], highlightthickness=1)
            card.grid(row=row, column=col, padx=(0, 15), pady=10, sticky='nsew')
            
            img_canvas = tk.Canvas(card, bg=self.theme['img_placeholder'], height=240, highlightthickness=0)
            img_canvas.pack(fill='x', padx=1, pady=1)
            
            image_filename = prod[3]
            img_path = os.path.join("assets", "products", image_filename) if image_filename else None
            
            if img_path and os.path.exists(img_path):
                def draw_image(event, path=img_path, canvas=img_canvas):
                    w, h = event.width, event.height
                    if w > 1 and h > 1:
                        try:
                            img = Image.open(path)
                            img = ImageOps.fit(img, (w, h), Image.Resampling.LANCZOS)
                            photo = ImageTk.PhotoImage(img)
                            canvas.delete("all")
                            canvas.create_image(w//2, h//2, image=photo)
                            canvas.image = photo 
                        except Exception as e:
                            print(f"Error drawing image: {e}")
                
                img_canvas.bind("<Configure>", draw_image)
            else:
                def draw_icon(event, canvas=img_canvas):
                    canvas.delete("all")
                    canvas.create_text(event.width//2, event.height//2, text="☕", fill=self.theme['text_muted'], font=("Segoe UI", 40))
                img_canvas.bind("<Configure>", draw_icon)
            
            info_frame = tk.Frame(card, bg=self.theme['bg_card'])
            info_frame.pack(fill='x', padx=15, pady=(10, 12))
            
            tk.Label(info_frame, text=prod[1], font=("Segoe UI", 13, "bold"), 
                     bg=self.theme['bg_card'], fg=self.theme['text_main'], 
                     wraplength=250, justify='left', anchor='w').pack(fill='x')
            
            bottom_row = tk.Frame(info_frame, bg=self.theme['bg_card'])
            bottom_row.pack(fill='x', pady=(8, 0))
            
            tk.Label(bottom_row, text=f"₱{prod[2]:.2f}", font=("Segoe UI", 11), 
                     bg=self.theme['bg_card'], fg=self.theme['text_muted']).pack(side='left')
            
            btn_canvas = tk.Canvas(bottom_row, width=32, height=32, bg=self.theme['bg_card'], highlightthickness=0, cursor="hand2")
            btn_canvas.pack(side='right')
            
            btn_canvas.create_oval(2, 2, 30, 30, fill=self.theme['accent'], outline="")
            btn_canvas.create_text(16, 16, text="+", fill=self.theme['accent_fg'], font=("Segoe UI", 16, "bold"))
            
            btn_canvas.bind("<Button-1>", lambda e, p=prod: self.add_to_cart(p))
            
            col += 1
            if col > 1: 
                col = 0
                row += 1
        
        for i in range(2):
            self.product_frame.grid_columnconfigure(i, weight=1)

        if not products:
            tk.Label(self.product_frame, text="No products found.", font=("Segoe UI", 14), 
                     bg=self.theme['bg_main'], fg=self.theme['text_muted']).grid(row=0, column=0, columnspan=2, pady=30)

    def add_to_cart(self, product):
        pid = product[0]
        if pid in self.cart:
            self.cart[pid]['qty'] += 1
        else:
            self.cart[pid] = {'name': product[1], 'price': float(product[2]), 'qty': 1}
        self.update_cart_display()

    def update_cart_display(self):
        for widget in self.cart_display.winfo_children():
            widget.destroy()

        total_items = sum(item['qty'] for item in self.cart.values())
        subtotal = sum(item['price'] * item['qty'] for item in self.cart.values())

        if total_items > 0:
            self.cart_summary_label.config(text=f"New sale • {len(self.cart)} products • {total_items} items")
        else:
            self.cart_summary_label.config(text="New sale")

        if not self.cart:
            tk.Label(self.cart_display, text="No items in current order.", font=("Segoe UI", 11),
                     bg=self.theme['cart_bg'], fg=self.theme['text_muted']).pack(pady=30)
        else:
            for pid, item in self.cart.items():
                item_frame = tk.Frame(self.cart_display, bg=self.theme['cart_bg'])
                item_frame.pack(fill='x', pady=(15, 5), padx=15)
                
                top_row = tk.Frame(item_frame, bg=self.theme['cart_bg'])
                top_row.pack(fill='x')
                tk.Label(top_row, text=item['name'], font=("Segoe UI", 11, "bold"), bg=self.theme['cart_bg'], fg=self.theme['text_main']).pack(side='left')
                
                item_total = item['price'] * item['qty']
                tk.Label(top_row, text=f"₱{item_total:.2f}", font=("Segoe UI", 11, "bold"), bg=self.theme['cart_bg'], fg=self.theme['text_main']).pack(side='right')
                
                bottom_row = tk.Frame(item_frame, bg=self.theme['cart_bg'])
                bottom_row.pack(fill='x', pady=(8,0))
                
                tk.Label(bottom_row, text=f"₱{item['price']:.2f} each", font=("Segoe UI", 9), bg=self.theme['cart_bg'], fg=self.theme['text_muted']).pack(side='left')
                
                controls_frame = tk.Frame(bottom_row, bg=self.theme['cart_bg'])
                controls_frame.pack(side='right')
                
                remove_lbl = tk.Label(controls_frame, text="Remove", font=("Segoe UI", 9, "underline"), bg=self.theme['cart_bg'], fg=self.theme['text_muted'], cursor="hand2")
                remove_lbl.pack(side='right', padx=(15, 0))
                remove_lbl.bind("<Button-1>", lambda e, p=pid: self.remove_item(p))
                
                qty_pill = tk.Frame(controls_frame, bg=self.theme['cart_bg'], highlightbackground=self.theme['border'], highlightthickness=1)
                qty_pill.pack(side='right')
                
                btn_minus = tk.Label(qty_pill, text="−", font=("Segoe UI", 11), bg=self.theme['cart_bg'], fg=self.theme['text_muted'], cursor="hand2", width=2, pady=2)
                btn_minus.pack(side='left')
                btn_minus.bind("<Button-1>", lambda e, p=pid: self.change_qty(p, -1))
                
                tk.Label(qty_pill, text=str(item['qty']), font=("Segoe UI", 10, "bold"), bg=self.theme['cart_bg'], fg=self.theme['text_main'], width=2).pack(side='left')
                
                btn_plus = tk.Label(qty_pill, text="+", font=("Segoe UI", 11), bg=self.theme['cart_bg'], fg=self.theme['text_muted'], cursor="hand2", width=2, pady=2)
                btn_plus.pack(side='left')
                btn_plus.bind("<Button-1>", lambda e, p=pid: self.change_qty(p, 1))

                tk.Frame(item_frame, height=1, bg=self.theme['divider']).pack(fill='x', pady=(10,0))

        self.subtotal_label_left.config(text=f"Subtotal • {total_items} items" if total_items > 0 else "Subtotal • 0 items")
        self.subtotal_label_right.config(text=f"₱{subtotal:.2f}")
        self.total_label.config(text=f"₱{subtotal:.2f}")
        self.pay_btn_right.config(text=f"₱{subtotal:.2f} ➔")

    def change_qty(self, product_id, delta):
        if product_id in self.cart:
            self.cart[product_id]['qty'] += delta
            if self.cart[product_id]['qty'] <= 0:
                del self.cart[product_id]
            self.update_cart_display()

    def remove_item(self, product_id):
        if product_id in self.cart:
            del self.cart[product_id]
            self.update_cart_display()

    def clear_cart(self):
        if not self.cart: return
        if messagebox.askyesno("Clear Order", "Are you sure you want to clear the current order?"):
            self.cart.clear()
            self.update_cart_display()

    def open_payment(self):
        if not self.cart:
            messagebox.showwarning("Empty Order", "Please add items to the order before proceeding to payment.")
            return
        try:
            order_type = self.order_type_var.get()
            PaymentWindow(self.root, self.user_data, self.cart, self.theme, order_type, self.on_payment_success)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open payment window:\n{str(e)}")

    def on_payment_success(self):
        self.cart.clear()
        self.order_type_var.set("Dine In")
        self.set_order_type("Dine In")
        self.update_cart_display()