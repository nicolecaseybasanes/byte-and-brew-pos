# services/transaction_service.py
from database.connection import get_db_connection
import datetime
from config.settings import RECEIPT_PREFIX

def generate_receipt_number(cursor):
    today_str = datetime.datetime.now().strftime("%Y%m%d")
    prefix = f"{RECEIPT_PREFIX}-{today_str}-"
    
    cursor.execute(
        "SELECT COUNT(*) FROM sales WHERE receipt_number LIKE ?",
        (f"{prefix}%",)
    )
    result = cursor.fetchone()
    count = result[0] if result else 0
    new_number = count + 1
    return f"{prefix}{new_number:04d}"

def save_sale(cashier_id, cart, payment_method, amount_received, customer_name, order_type):
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed.", None

    cursor = conn.cursor()
    try:
        subtotal = sum(item['price'] * item['qty'] for item in cart.values())
        total = subtotal
        change = amount_received - total
        
        if payment_method == 'Cash' and change < 0:
            return False, "Insufficient payment amount.", None

        receipt_number = generate_receipt_number(cursor)

        # Added customer_name and order_type to the INSERT statement
        sale_query = """
            INSERT INTO sales 
            (receipt_number, cashier_id, customer_name, order_type, subtotal, total_amount, payment_method, amount_received, change_amount, payment_status, sale_status)
            OUTPUT INSERTED.sale_id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Paid', 'Completed')
        """
        cursor.execute(sale_query, (receipt_number, cashier_id, customer_name, order_type, subtotal, total, payment_method, amount_received, change))
        
        row = cursor.fetchone()
        if not row or row[0] is None:
            raise Exception("Failed to retrieve new sale ID from database.")
        sale_id = int(row[0])

        item_query = """
            INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, subtotal)
            VALUES (?, ?, ?, ?, ?)
        """
        for pid, item in cart.items():
            cursor.execute(item_query, (sale_id, pid, item['qty'], item['price'], item['price'] * item['qty']))

        conn.commit()
        return True, "Transaction saved successfully.", receipt_number

    except Exception as e:
        conn.rollback()
        print(f"Transaction error: {e}")
        return False, f"Transaction failed: {e}", None
    finally:
        cursor.close()
        conn.close()