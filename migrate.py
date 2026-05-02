import sqlite3

def migrate():
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE expenses ADD COLUMN billing_cycle VARCHAR DEFAULT 'Monthly'")
        conn.commit()
        print("Successfully added billing_cycle column to expenses table.")
    except sqlite3.OperationalError as e:
        print(f"Error (maybe column already exists?): {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
