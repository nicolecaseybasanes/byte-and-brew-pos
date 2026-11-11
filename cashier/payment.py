# cashier/payment.py
import tkinter as tk
from tkinter import messagebox
from services.transaction_service import save_sale
from cashier.receipt import ReceiptWindow

class PaymentWindow:
    def __init__(self, parent, user_data, cart, theme, order_type, on_success):
        self.parent = parent
        self.user_data = user_data
        self.cart = cart
        self.theme = theme 
        self.order_type = order_type
        self.on_success = on_success 

        self.total = sum(item['price'] * item['qty'] for item in cart.values())

        self.window = tk.Toplevel(parent)
        self.window.title("Payment")
        self.window.transient(parent) 
        self.window.lift()            
        
        width, height = 420, 620 
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
        self.window.configure(bg=self.theme['bg_main'])
        self.window.grab_set()
        self.window.resizable(False, False)

        self.method_var = tk.StringVar(value="Cash")
        
        self.create_widgets()

    def create_widgets(self):
        card = tk.Frame(self.window, bg=self.theme['bg_card'], padx=30, pady=30, highlightbackground=self.theme['border'], highlightthickness=1)
        card.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(card, text="PAYMENT", font=("Segoe UI", 20, "bold"), bg=self.theme['bg_card'], fg=self.theme['text_main']).pack(pady=(0, 20))

        tk.Label(card, text="Total Amount", font=("Segoe UI", 11), bg=self.theme['bg_card'], fg=self.theme['text_muted']).pack()
        tk.Label(card, text=f"₱{self.total:.2f}", font=("Segoe UI", 28, "bold"), fg=self.theme['accent'], bg=self.theme['bg_card']).pack(pady=(0, 20))

        # --- CUSTOMER NAME (Mandatory) ---
        tk.Label(card, text="Customer Name *", font=("Segoe UI", 10, "bold"), bg=self.theme['bg_card'], fg=self.theme['text_main'], anchor='w').pack(fill='x')
        self.customer_entry = tk.Entry(card, font=("Segoe UI", 14), bg=self.theme['bg_main'], fg=self.theme['text_main'], 
                                     relief="flat", insertbackground=self.theme['text_main'], highlightbackground=self.theme['border'], highlightthickness=1)
        self.customer_entry.pack(fill='x', pady=(5, 15), ipady=6)
        self.customer_entry.focus_set() # Focus here first

        # Payment Method
        tk.Label(card, text="Payment Method", font=("Segoe UI", 10, "bold"), bg=self.theme['bg_card'], fg=self.theme['text_main'], anchor='w').pack(fill='x')
        
        method_frame = tk.Frame(card, bg=self.theme['bg_card'])
        method_frame.pack(fill='x', pady=(5, 15))
        
        radio_style = {
            "font": ("Segoe UI", 11, "bold"),
            "bg": self.theme['bg_card'],
            "fg": self.theme['text_main'],
            "selectcolor": self.theme['bg_main'],
            "activebackground": self.theme['bg_card'],
            "activeforeground": self.theme['text_main'],
            "highlightthickness": 0,
            "bd": 0,
            "cursor": "hand2",
            "command": self.update_fields
        }

        tk.Radiobutton(method_frame, text="CASH", variable=self.method_var, value="Cash", **radio_style).pack(side='left', padx=(0, 30))
        tk.Radiobutton(method_frame, text="GCASH", variable=self.method_var, value="GCash", **radio_style).pack(side='left')

        # Amount Received
        tk.Label(card, text="Amount Received", font=("Segoe UI", 10, "bold"), bg=self.theme['bg_card'], fg=self.theme['text_main'], anchor='w').pack(fill='x')
        
        self.amount_entry = tk.Entry(card, font=("Segoe UI", 16), bg=self.theme['bg_main'], fg=self.theme['text_main'], 
                                     relief="flat", insertbackground=self.theme['text_main'], highlightbackground=self.theme['border'], highlightthickness=1)
        self.amount_entry.pack(fill='x', pady=(5, 15), ipady=6)
        
        self.amount_entry.bind('<KeyRelease>', self.calculate_change)

        # Change
        tk.Label(card, text="Change", font=("Segoe UI", 10, "bold"), bg=self.theme['bg_card'], fg=self.theme['text_main'], anchor='w').pack(fill='x')
        self.change_label = tk.Label(card, text="₱0.00", font=("Segoe UI", 20, "bold"), bg=self.theme['bg_card'], fg=self.theme['text_muted'], anchor='w')
        self.change_label.pack(fill='x', pady=(5, 20))

        # Action Buttons
        btn_frame = tk.Frame(card, bg=self.theme['bg_card'])
        btn_frame.pack(fill='x')
        
        tk.Button(btn_frame, text="CANCEL", font=("Segoe UI", 11, "bold"), bg=self.theme['btn_secondary'], fg=self.theme['btn_secondary_text'],
                  relief="flat", cursor="hand2", command=self.window.destroy).pack(side='left', expand=True, fill='x', padx=(0, 5), ipady=8)
        
        tk.Button(btn_frame, text="COMPLETE PAYMENT", font=("Segoe UI", 11, "bold"), bg=self.theme['accent'], fg=self.theme['accent_fg'],
                  activebackground=self.theme['accent_hover'], activeforeground=self.theme['accent_fg'], relief="flat", cursor="hand2",
                  command=self.process_payment).pack(side='right', expand=True, fill='x', padx=(5, 0), ipady=8)

    def update_fields(self):
        if self.method_var.get() == "GCash":
            self.amount_entry.config(state='normal')
            self.amount_entry.delete(0, 'end')
            self.amount_entry.insert(0, f"{self.total:.2f}")
            self.amount_entry.bind('<Key>', lambda e: "break")
            self.amount_entry.unbind('<KeyRelease>')
        else:
            self.amount_entry.config(state='normal')
            self.amount_entry.delete(0, 'end')
            self.amount_entry.unbind('<Key>')
            self.amount_entry.bind('<KeyRelease>', self.calculate_change)
        self.calculate_change()

    def calculate_change(self, event=None):
        if self.method_var.get() == "GCash":
            change = 0.00
            self.change_label.config(text="₱0.00", fg=self.theme['text_muted'])
        else:
            try:
                received = float(self.amount_entry.get() or 0)
                change = received - self.total
                if change < 0:
                    self.change_label.config(text="Insufficient", fg="#EF4444")
                else:
                    self.change_label.config(text=f"₱{change:.2f}", fg=self.theme['text_muted'])
            except ValueError:
                change = 0.00
                self.change_label.config(text="₱0.00", fg=self.theme['text_muted'])

    def process_payment(self):
        method = self.method_var.get()
        
        # Enforce Customer Name
        customer_name = self.customer_entry.get().strip()
        if not customer_name:
            messagebox.showerror("Validation Error", "Customer name is required.", parent=self.window)
            return

        try:
            received = float(self.amount_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid amount.", parent=self.window)
            return

        # Pass order_type and customer_name to save_sale
        success, message, receipt_number = save_sale(
            self.user_data['user_id'], self.cart, method, received, customer_name, self.order_type
        )

        if success:
            self.window.destroy()
            ReceiptWindow(
                self.parent, receipt_number, self.cart, method, received, 
                received - self.total, customer_name, self.order_type, self.theme
            )
            self.on_success() 
        else:
            messagebox.showerror("Transaction Failed", message, parent=self.window)