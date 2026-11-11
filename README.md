# Byte and Brew: Restaurant POS & Sales Monitoring System

A comprehensive, desktop-based Point of Sale (POS) and Sales Monitoring System built for restaurant operations. It features a modern, responsive UI with built-in Dark/Light mode, secure role-based access, and real-time sales analytics.

> **Note:** This is a **desktop application** built with Python and Tkinter. It is not a web application and is intended to run locally on Windows machines.

## Features

*   **Role-Based Access Control:** Distinct roles for **Admin/Owner** and **Cashier** with enforced permissions.
*   **Modern Cashier POS:** Fast, intuitive menu with category filters, live search, product images, and a dynamic cart. Supports **Dine-In** and **Take-Out**.
*   **Payment Processing:** Cash and GCash support with automatic change calculation.
*   **Printable Receipts:** Generates formatted HTML receipts ready for thermal printing.
*   **Admin Dashboard:** Real-time sales analytics using **Matplotlib**, tracking daily, weekly, monthly, and yearly trends, alongside best-selling products.
*   **Employee & Product Management:** Full CRUD (Create, Read, Update, Delete) capabilities for staff accounts and menu items.
*   **Secure:** Passwords are securely hashed using `bcrypt`. Database credentials are hidden using `.env` variables.

## Tech Stack

*   **Frontend/GUI:** Python, Tkinter, TTK
*   **Database:** Microsoft SQL Server (SSMS)
*   **Data Visualization:** Matplotlib
*   **Security:** bcrypt
*   **Database Connector:** pyodbc
*   **Image Processing:** Pillow (PIL)

## Screenshots



### Role Selection & Login
![Role Selection](INSERT_IMAGE_LINK_HERE)
![Login Screen](INSERT_IMAGE_LINK_HERE)

### Cashier POS (Light & Dark Mode)
![Cashier POS Light](INSERT_IMAGE_LINK_HERE)
![Cashier POS Dark](INSERT_IMAGE_LINK_HERE)

### Admin Dashboard
![Admin Dashboard](INSERT_IMAGE_LINK_HERE)

### Employee Management
![Employee Management](INSERT_IMAGE_LINK_HERE)

##  How to Run Locally

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/byte_and_brew_pos.git