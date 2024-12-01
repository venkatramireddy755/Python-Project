import sqlite3
import bcrypt
import datetime
from rich.console import Console
from rich.table import Table

console = Console()

# Database Initialization
def initialize_database():
    conn = sqlite3.connect('finance_manager.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS Users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL
                      )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS Transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        type TEXT,
                        category TEXT,
                        amount REAL,
                        date TEXT,
                        FOREIGN KEY(user_id) REFERENCES Users(id)
                      )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS Budgets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        category TEXT,
                        budget_limit REAL,
                        FOREIGN KEY(user_id) REFERENCES Users(id)
                      )''')

    conn.commit()
    conn.close()

# User Registration
def register_user():
    print("Register a new account")
    username = input("Enter a new username: ")
    password = input("Enter a new password: ")
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        conn = sqlite3.connect('finance_manager.db')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Users WHERE username = ?", (username,))
        if cursor.fetchone():
            print("Username already exists! Please choose a different one.")
            return

        cursor.execute("INSERT INTO Users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        print(f"Registration successful! Welcome, {username}!")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

# User Login
def login_user():
    print("Login to your account")
    conn = sqlite3.connect('finance_manager.db')
    cursor = conn.cursor()

    while True:
        username = input("Enter username: ")

        # Retrieve the user data based on the username
        cursor.execute("SELECT id, password FROM Users WHERE username = ?", (username,))
        result = cursor.fetchone()

        if result:
            user_id, stored_password = result

            while True:
                password = input("Enter password: ")
                if bcrypt.checkpw(password.encode('utf-8'), stored_password):
                    print("Login successful!")
                    conn.close()
                    return user_id
                else:
                    print("Incorrect password. Please try again.")
        else:
            print("Username not found. Please enter a valid username.")



# Add Transaction
def add_transaction(user_id, type_):
    print(f"Adding a new {type_}")
    category = input("Enter the category (e.g., Food, Rent, Salary): ")
    amount = float(input("Enter the amount: "))
    date = input(f"Enter the date (YYYY-MM-DD, default: {datetime.date.today()}): ") or str(datetime.date.today())

    conn = sqlite3.connect('finance_manager.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Transactions (user_id, type, category, amount, date) VALUES (?, ?, ?, ?, ?)",
                   (user_id, type_, category, amount, date))
    conn.commit()
    conn.close()
    print(f"{type_.capitalize()} added successfully!")

# Delete Transaction
def delete_transaction(user_id):
    trans_id = int(input("Enter the transaction ID to delete: "))
    conn = sqlite3.connect('finance_manager.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Transactions WHERE id = ? AND user_id = ?", (trans_id, user_id))
    conn.commit()
    conn.close()
    print("Transaction deleted successfully!")

# Generate Financial Report
def generate_report(user_id, period='monthly'):
    print(f"Generating {period} report")
    conn = sqlite3.connect('finance_manager.db')
    cursor = conn.cursor()

    if period == 'monthly':
        month = input("Enter month (MM): ")
        year = input("Enter year (YYYY): ")
        cursor.execute('''SELECT type, SUM(amount) FROM Transactions 
                          WHERE user_id = ? AND strftime('%m', date) = ? 
                          AND strftime('%Y', date) = ? GROUP BY type''',
                       (user_id, month, year))
    else:
        year = input("Enter year (YYYY): ")
        cursor.execute('''SELECT type, SUM(amount) FROM Transactions 
                          WHERE user_id = ? AND strftime('%Y', date) = ? 
                          GROUP BY type''', (user_id, year))

    report = cursor.fetchall()
    conn.close()

    table = Table(title=f"{period.capitalize()} Financial Report")
    table.add_column("Type", justify="center")
    table.add_column("Total Amount", justify="center")

    total_income = total_expenses = 0
    for row in report:
        table.add_row(row[0], f"{row[1]:.2f}")
        if row[0] == "income":
            total_income += row[1]
        elif row[0] == "expense":
            total_expenses += row[1]

    savings = total_income - total_expenses
    console.print(table)
    print(f"Total Income: {total_income}")
    print(f"Total Expenses: {total_expenses}")
    print(f"Savings: {savings}")

# Set Budget
def set_budget(user_id):
    print("Set Budget for a Category")
    category = input("Enter category for budget (e.g., Food): ")
    budget_limit = float(input("Enter budget limit: "))

    conn = sqlite3.connect('finance_manager.db')
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO Budgets (user_id, category, budget_limit) VALUES (?, ?, ?)",
                   (user_id, category, budget_limit))
    conn.commit()
    conn.close()
    print(f"Budget set for {category} category.")

def show_balance(user_id):
    conn = sqlite3.connect('finance_manager.db')
    cursor = conn.cursor()

    # Calculate total income
    cursor.execute(
        "SELECT SUM(amount) FROM Transactions WHERE user_id = ? AND type = 'income'",
        (user_id,)
    )
    total_income = cursor.fetchone()[0] or 0.0

    # Calculate total expenses
    cursor.execute(
        "SELECT SUM(amount) FROM Transactions WHERE user_id = ? AND type = 'expense'",
        (user_id,)
    )
    total_expenses = cursor.fetchone()[0] or 0.0

    # Calculate balance
    balance = total_income - total_expenses

    conn.close()

    # Display the balance
    print("\n--- Balance Summary ---")
    print(f"Total Income: {total_income:.2f}")
    print(f"Total Expenses: {total_expenses:.2f}")
    print(f"Current Balance: {balance:.2f}")
    print("-----------------------")


# Main Program Loop
def main():
    initialize_database()
    print("Welcome to Personal Finance Manager")
    user_id = None

    while True:
        if not user_id:
            print("1: Register\n2: Login")
            choice = input("Choose an option: ")
            if choice == '1':
                register_user()
            elif choice == '2':
                user_id = login_user()
        else:
            print("1: Add Income\n2: Add Expense\n3: Delete Transaction\n4: Generate Report\n5: Set Budget\n6: Balance \n7: Logout")
            choice = input("Choose an option: ")
            if choice == '1':
                add_transaction(user_id, "income")
            elif choice == '2':
                add_transaction(user_id, "expense")
            elif choice == '3':
                delete_transaction(user_id)
            elif choice == '4':
                period = input("Enter period (monthly/yearly): ")
                generate_report(user_id, period)
            elif choice == '5':
                set_budget(user_id)
            elif choice == '6':
                show_balance(user_id)
            elif choice == '7':
                user_id = None
                print("Logged out.")

if __name__ == '__main__':
    main()

