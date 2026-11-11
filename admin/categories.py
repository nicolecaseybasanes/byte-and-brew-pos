# admin/categories.py
import tkinter as tk
from tkinter import ttk, messagebox
from config.settings import LIGHT_THEME, DARK_THEME
from database.connection import get_db_connection

class CategoryManager:
    def __init__(self, parent_frame, theme):
        self.parent = parent_frame
        self.theme = theme
        
        self.create_ui()
        self.load_categories()

    def create_ui(self):
        self.parent.configure(bg=self.theme['bg_main'])
        
        # Header
        header_frame = tk.Frame(self.parent, bg=self.theme['bg_main'])
        header_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(header_frame, text="Categories", font=("Segoe UI", 22, "bold"),
                 bg=self.theme['bg_main'], fg=self.theme['text_main']).pack(side='left')
                 
        tk.Button(header_frame, text="+ Add Category", font=("Segoe UI", 10, "bold"),
                  bg=self.theme['accent'], fg=self.theme['accent_fg'],
                  activebackground=self.theme['accent_hover'], activeforeground=self.theme['accent_fg'],
                  relief="flat", cursor="hand2", padx=15, pady=8,
                  command=self.open_add_category_window).pack(side='right')

        # Main Layout (Split view)
        main_content = tk.Frame(self.parent, bg=self.theme['bg_main'])
        main_content.pack(fill='both', expand=True)

        # Left: Table
        table_container = tk.Frame(main_content, bg=self.theme['bg_card'], highlightbackground=self.theme['border'], highlightthickness=1)
        table_container.pack(side='left', fill='both', expand=True, padx=(0, 15))

        action_frame = tk.Frame(table_container, bg=self.theme['bg_card'])
        action_frame.pack(fill='x', padx=15, pady=15)

        tk.Button(action_frame, text="Delete (Empty Only)", font=("Segoe UI", 9), bg=self.theme['btn_secondary'], fg=self.theme['btn_secondary_text'],
                  command=self.delete_category).pack(side='right', padx=5)
        tk.Button(action_frame, text="Archive / Activate", font=("Segoe UI", 9), bg=self.theme['btn_secondary'], fg=self.theme['btn_secondary_text'],
                  command=self.toggle_availability).pack(side='right', padx=5)
        tk.Button(action_frame, text="Edit Selected", font=("Segoe UI", 9), bg=self.theme['btn_secondary'], fg=self.theme['btn_secondary_text'],
                  command=self.open_edit_category_window).pack(side='right', padx=5)

        # Treeview
        tree_frame = tk.Frame(table_container, bg=self.theme['bg_card'])
        tree_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=self.theme['bg_card'], foreground=self.theme['text_main'], rowheight=35, fieldbackground=self.theme['bg_card'], font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background=self.theme['bg_main'], foreground=self.theme['text_muted'], font=("Segoe UI", 8, "bold"))
        style.map("Treeview", background=[('selected', self.theme['accent'])], foreground=[('selected', self.theme['accent_fg'])])

        columns = ("ID", "Category Name", "Status")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.tree.heading(col, text=col.upper())
            self.tree.column(col, anchor='w')
            
        self.tree.pack(fill='both', expand=True)
        self.tree.bind("<Double-1>", lambda e: self.open_edit_category_window())

    def load_categories(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor()
        cursor.execute("SELECT category_id, category_name, is_active FROM categories ORDER BY category_name")
        categories = cursor.fetchall()
        cursor.close()
        conn.close()

        for cat in categories:
            status = "Active" if cat[2] else "Archived"
            self.tree.insert('', 'end', values=(cat[0], cat[1], status))

    def get_selected_category(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection", "Please select a category first.", parent=self.parent)
            return None
        return self.tree.item(selected[0])['values']

    def toggle_availability(self):
        cat = self.get_selected_category()
        if not cat: return

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE categories SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE category_id = ?", (cat[0],))
            conn.commit()
            self.load_categories()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", str(e), parent=self.parent)
        finally:
            cursor.close()
            conn.close()

    def delete_category(self):
        cat = self.get_selected_category()
        if not cat: return

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM products WHERE category_id = ?", (cat[0],))
            product_count = cursor.fetchone()[0]

            if product_count > 0:
                messagebox.showerror("Cannot Delete", f"This category is being used by {product_count} product(s).\n\nYou can only 'Archive' it.", parent=self.parent)
                return

            confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to permanently delete '{cat[1]}'?", parent=self.parent)
            if confirm:
                cursor.execute("DELETE FROM categories WHERE category_id = ?", (cat[0],))
                conn.commit()
                self.load_categories()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", str(e), parent=self.parent)
        finally:
            cursor.close()
            conn.close()

    def open_add_category_window(self):
        self.show_category_form("Add Category")

    def open_edit_category_window(self):
        cat = self.get_selected_category()
        if cat:
            self.show_category_form("Edit Category", cat)

    def show_category_form(self, title, category_data=None):
        win = tk.Toplevel(self.parent)
        win.title(title)
        
        width, height = 350, 250
        x = (win.winfo_screenwidth() // 2) - (width // 2)
        y = (win.winfo_screenheight() // 2) - (height // 2)
        win.geometry(f'{width}x{height}+{x}+{y}')
        
        win.configure(bg=self.theme['bg_main'])
        win.grab_set()

        card = tk.Frame(win, bg=self.theme['bg_card'], padx=20, pady=20, highlightbackground=self.theme['border'], highlightthickness=1)
        card.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(card, text=title, font=("Segoe UI", 14, "bold"), bg=self.theme['bg_card'], fg=self.theme['text_main']).pack(pady=(0, 15))

        tk.Label(card, text="Category Name", font=("Segoe UI", 9, "bold"), bg=self.theme['bg_card'], fg=self.theme['text_main'], anchor='w').pack(fill='x')
        name_entry = tk.Entry(card, font=("Segoe UI", 12), bg=self.theme['bg_main'], fg=self.theme['text_main'], relief="flat", highlightbackground=self.theme['border'], highlightthickness=1)
        name_entry.pack(fill='x', pady=(5, 15), ipady=5)
        if category_data: 
            name_entry.insert(0, category_data[1])

        def save():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Category name is required.", parent=win)
                return

            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                if category_data:
                    cursor.execute("UPDATE categories SET category_name=? WHERE category_id=?", (name, category_data[0]))
                else:
                    cursor.execute("INSERT INTO categories (category_name) VALUES (?)", (name,))
                conn.commit()
                win.destroy()
                self.load_categories()
            except Exception as e:
                conn.rollback()
                messagebox.showerror("Database Error", f"Category might already exist.\n{str(e)}", parent=win)
            finally:
                cursor.close()
                conn.close()

        tk.Button(card, text="SAVE", font=("Segoe UI", 11, "bold"), bg=self.theme['accent'], fg=self.theme['accent_fg'],
                  relief="flat", cursor="hand2", command=save).pack(fill='x', ipady=5)