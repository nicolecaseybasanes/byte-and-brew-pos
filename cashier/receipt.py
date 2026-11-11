# cashier/receipt.py
import tkinter as tk
from tkinter import messagebox
import datetime
import os

class ReceiptWindow:
    def __init__(self, parent, receipt_number, cart, method, received, change, customer_name, order_type, theme):
        self.theme = theme
        self.window = tk.Toplevel(parent)
        self.window.title(f"Receipt - {receipt_number}")
        self.window.transient(parent) 
        self.window.lift()            
        
        width, height = 450, 650
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
        self.window.configure(bg=self.theme['bg_main'])
        self.window.grab_set()

        self.receipt_number = receipt_number
        self.cart = cart
        self.method = method
        self.received = received
        self.change = change
        self.customer_name = customer_name
        self.order_type = order_type

        self.customer_text = self.generate_customer_receipt()
        self.create_widgets()

    def generate_customer_receipt(self):
        now = datetime.datetime.now()
        lines = []
        lines.append("        BYTE AND BREW")
        lines.append("       Restaurant POS")
        lines.append("--------------------------------")
        lines.append(f"Receipt No: {self.receipt_number}")
        lines.append(f"Date: {now.strftime('%m/%d/%Y')}")
        lines.append(f"Time: {now.strftime('%I:%M %p')}")
        lines.append(f"Customer: {self.customer_name}")
        lines.append(f"Order Type: {self.order_type}") # Added Order Type
        lines.append("--------------------------------")
        
        total = 0
        for item in self.cart.values():
            subtotal = item['price'] * item['qty']
            total += subtotal
            name = item['name'][:15]
            lines.append(f"{name:<15} {item['qty']} x {item['price']:.2f} = {subtotal:.2f}")
        
        lines.append("--------------------------------")
        lines.append(f"Subtotal:              PHP {total:.2f}")
        lines.append(f"TOTAL:                 PHP {total:.2f}")
        lines.append(f"Payment:               {self.method}")
        lines.append(f"Amount Received:       PHP {self.received:.2f}")
        lines.append(f"Change:                PHP {self.change:.2f}")
        lines.append("--------------------------------")
        lines.append("         Thank you!")
        return "\n".join(lines)

    def create_widgets(self):
        card = tk.Frame(self.window, bg=self.theme['bg_card'], padx=10, pady=10)
        card.pack(fill='both', expand=True, padx=20, pady=(20, 10))

        text_widget = tk.Text(card, font=("Courier New", 10), bg=self.theme['bg_card'], fg=self.theme['text_main'], 
                              relief="flat", padx=10, pady=10, highlightthickness=0)
        text_widget.insert('1.0', self.customer_text)
        text_widget.config(state='disabled')
        text_widget.pack(fill='both', expand=True)

        btn_frame = tk.Frame(self.window, bg=self.theme['bg_main'])
        btn_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        tk.Button(btn_frame, text="PRINT RECEIPT", font=("Segoe UI", 10, "bold"), bg=self.theme['accent'], fg=self.theme['accent_fg'],
                  relief="flat", cursor="hand2", command=lambda: self.print_via_browser(self.customer_text, "Customer")).pack(side='left', expand=True, fill='x', padx=(0, 10), ipady=5)
        
        tk.Button(btn_frame, text="CLOSE", font=("Segoe UI", 10, "bold"), bg=self.theme['btn_secondary'], fg=self.theme['btn_secondary_text'],
                  relief="flat", cursor="hand2", command=self.window.destroy).pack(side='right', expand=True, fill='x', padx=(10, 0), ipady=5)

    def print_via_browser(self, text_content, copy_type):
        try:
            save_dir = r"C:\ByteAndBrew_Receipts"
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            
            filename = os.path.join(save_dir, f"receipt_{self.receipt_number}_{copy_type}.html")
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{copy_type} Receipt - {self.receipt_number}</title>
                <style>
                    body {{
                        font-family: 'Courier New', Courier, monospace;
                        font-size: 14px;
                        width: 300px;
                        margin: 0 auto;
                        padding: 20px;
                        color: #000;
                    }}
                    pre {{
                        white-space: pre-wrap;
                        word-wrap: break-word;
                    }}
                    @media print {{
                        body {{
                            width: 100%;
                            margin: 0;
                            padding: 0;
                        }}
                    }}
                </style>
            </head>
            <body onload="window.print()">
                <pre>{text_content}</pre>
            </body>
            </html>
            """
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            os.startfile(filename)
            
        except Exception as e:
            messagebox.showerror("Print Error", f"Could not open receipt: {str(e)}", parent=self.window)