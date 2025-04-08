import sqlite3
from GlobalAccess import LogMsg, GetElevation, GetUser
import bcrypt

from datetime import datetime

def print_all_tables_with_entries(db_path):
    """
    Prints all tables in the SQLite database along with their entries.

    :param db_path: Path to the SQLite database file.
    """
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        if not tables:
            print("No tables found in the database.")
            return

        # Iterate through tables and print entries
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            print("-" * (len(table_name) + 8))

            cursor.execute(f"SELECT * FROM {table_name};")
            rows = cursor.fetchall()

            if rows:
                # Get column names
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = [col[1] for col in cursor.fetchall()]
                
                # Print column headers
                print(" | ".join(columns))
                print("-" * (len(" | ".join(columns)) + 5))

                # Print rows
                for row in rows:
                    print(" | ".join(str(value) for value in row))
            else:
                print("No entries found.")

        # Close the connection
        conn.close()

    except Exception as e:
        print(f"Error: {e}")


class DataBase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        # turn on foreign key support
        self.cursor.execute("PRAGMA foreign_keys = ON;")

        self.cursor.execute(f"PRAGMA table_info(product)")
        self.product_columns = [row[1] for row in self.cursor.fetchall()]

    def execute_sql_file(self, sql_file):
        try:
            with open(sql_file, 'r', encoding='utf-8') as file:
                sql_script = file.read()

            self.cursor.executescript(sql_script)
            # print result
            print(self.cursor.fetchall())

            # self.conn.commit()
            print("SQL script executed successfully.")

        except Exception as e:
            print(f"Error: {e}")

    def get_user_data(self, username):
        """Check login credentials."""
        try:
            self.cursor.execute("SELECT password, role_name FROM users WHERE username = ?", (username,))
        except Exception as e:
            LogMsg("Error getting user data : " + str(e))
            raise e
        result = self.cursor.fetchone()
        return result if result else None
    
    def get_users(self):
        try:
            self.cursor.execute("SELECT * FROM users;")
        except Exception as e:
            LogMsg("Error getting users : " + str(e))
            raise e
        return self.cursor.fetchall()
    
    def add_user(self, username, password, role):
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        try:
            self.cursor.execute(f"INSERT INTO users (username, password, role_name) VALUES ('{username}', '{hashed_pw}', '{role}');")
            self.conn.commit()
            LogMsg("User added successfully")
        except Exception as e:
            self.conn.rollback()
            LogMsg("Error adding user : " + str(e))
    
    def delete_user(self, user_id):
        try:
            self.cursor.execute(f"DELETE FROM users WHERE user_id = {user_id};")
            self.conn.commit()
            LogMsg("User deleted successfully")
        except Exception as e:
            LogMsg("Error deleting user : " + str(e))
    




    def addProduct(self, product_id, name, hsn, price, stock, unit, tax_perc, desc):
        # check if product id exists
        self.cursor.execute(f"SELECT * FROM product WHERE p_id = {product_id};")
        if self.cursor.fetchone():
            return LogMsg("Product ID already exists")
        
        try: price = float(price)
        except: return LogMsg("Invalid price value")
        try: stock = float(stock) 
        except: return LogMsg("Invalid stock value")
        try: tax_perc = float(tax_perc)
        except: return LogMsg("Invalid tax value")

        insert_query = f"INSERT INTO product VALUES ({product_id}, '{name}', '{hsn}', {price}, {stock}, '{unit}', {tax_perc}, '{desc}');"
        try:
            self.cursor.execute(insert_query)
            self.conn.commit()
            return LogMsg("Product added successfully")
        except Exception as e:
            self.conn.rollback()
            return LogMsg("Error adding product : " + str(e))

    def getProducts(self):
        self.cursor.execute("SELECT * FROM product;")
        return self.cursor.fetchall()
    
    def updateProduct(self, product_id, column_idx, new_value):
        if(column_idx == 0):
            try:
                # readd entry with new primary key
                self.cursor.execute(f"SELECT * FROM product WHERE p_id = {product_id};")
                product = self.cursor.fetchone()
                # delete old entry
                self.cursor.execute(f"DELETE FROM product WHERE p_id = {product_id};")
                self.cursor.execute(f"INSERT INTO product VALUES ({new_value}, '{product[1]}', {product[2]}, {product[3]}, '{product[4]}');")
                self.conn.commit()
                return LogMsg("Product updated successfully")
            except Exception as e:
                self.conn.rollback()
                return LogMsg("Updating product failed : " + str(e))

        else:
            try:
                column_name = self.product_columns[column_idx]
                self.cursor.execute(f"UPDATE product SET {column_name} = '{new_value}' WHERE p_id = {product_id};")
                self.conn.commit()
                return LogMsg("Product updated successfully")
            except Exception as e:
                self.conn.rollback()
                return LogMsg("Error updating product: " + str(e))
    
    def deleteProduct(self, product_id):
        self.cursor.execute(f"DELETE FROM product WHERE p_id = {product_id};")
        self.conn.commit()
        LogMsg("Product(s) deleted successfully")

    def searchProducts(self, search_query):
        self.cursor.execute(f"SELECT * FROM product WHERE p_name LIKE '%{search_query}%' OR p_id LIKE '%{search_query}%';")
        return self.cursor.fetchall()
    
    def getCurrentBill(self):
        self.cursor.execute("SELECT * FROM curr_bill;")
        return self.cursor.fetchall()
    
    def clearCurrentBill(self):
        self.cursor.execute("DELETE FROM curr_bill;")
        self.conn.commit()
        LogMsg("Bill cleared")
    
    def addItemToBill(self, product_id, quantity, override=True):
        addquery = f"\
INSERT INTO curr_bill (p_id, p_name, HSN, unit_price, quantity, unit, tax_perc) \
SELECT {product_id}, p_name, HSN, price, {quantity}, unit, tax_perc \
FROM product \
WHERE p_id = {product_id} \
ON CONFLICT(p_id, p_name) DO UPDATE \
SET quantity = excluded.quantity \
;"
        try:
            if override:
                if quantity == 0:
                    self.removeItemFromBill(product_id)
                    return

                self.cursor.execute(addquery)
                self.conn.commit()
                LogMsg(f"Product {product_id} quantity set to: {quantity}")
            else:
                self.cursor.execute(f"SELECT * FROM curr_bill WHERE p_id = {product_id};")
                item = self.cursor.fetchone()
                if not item:
                    self.cursor.execute(addquery)
                    LogMsg(f"Product {product_id} added to bill. Enter quantity")
        except Exception as e:
            return LogMsg("Error adding item to bill : " + str(e))
        

    def removeItemFromBill(self, id):
        self.cursor.execute(f"DELETE FROM curr_bill WHERE p_id = {id};")
        self.conn.commit()
        LogMsg(f"Product {id} removed form bill")

    def getNextBillId(self):
        self.cursor.execute("SELECT IFNULL(MAX(bill_id), 0) + 1 FROM bills;")
        return self.cursor.fetchone()[0]

    def save_bill(self):
        query = f"\
BEGIN TRANSACTION;\
INSERT INTO bills (creator) VALUES ('{GetUser()}');\
INSERT INTO bill_items (bill_id, p_id, p_name, HSN, unit_price, quantity, unit, tax_perc) \
SELECT (SELECT last_insert_rowid()), p_id, p_name, HSN, unit_price, quantity, unit, tax_perc FROM curr_bill;\
UPDATE product \
SET stock = stock - (SELECT quantity FROM curr_bill WHERE curr_bill.p_id = product.p_id) \
WHERE p_id IN (SELECT p_id FROM curr_bill); \
COMMIT;"
        try:
            invoice_no = self.getNextBillId()
            self.cursor.executescript(query)
            LogMsg("bill saved to database. stock updated")
            return invoice_no
        except Exception as e:
            self.conn.rollback()
            LogMsg("failed to save bill to database : " + str(e))

    def get_bill_date(self, bill_id):
        self.cursor.execute(f"SELECT timestamp FROM bills WHERE bill_id = {bill_id};")
        timestamp_str = self.cursor.fetchone()[0]
        return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

    def get_bills(self):
        self.cursor.execute("SELECT * FROM bills ORDER BY timestamp DESC;")
        return self.cursor.fetchall()
    
    def get_bill_items(self, bill_id):
        self.cursor.execute(f"SELECT p_id, p_name, HSN, unit_price, quantity, unit, tax_perc FROM bill_items WHERE bill_id = {bill_id};")
        return self.cursor.fetchall()
    
    def delete_bill(self, bill_id):
        self.cursor.execute("DELETE FROM bills WHERE bill_id = ?", (bill_id,))
        self.conn.commit()

    def bootstrap(self):
        try:
            self.execute_sql_file('database/test.sql')
        except Exception as e:
            LogMsg("Error bootstrapping database : " + str(e))
            return
        
        username = 'admin'
        password = 'admin'
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        self.cursor.execute(f"INSERT INTO users (username, password, role_name) VALUES ('{username}', '{hashed_pw}', 'admin')")
        self.conn.commit()
    
    def get_curr_date(self):
        self.cursor.execute("SELECT datetime('now', 'localtime');")
        return self.cursor.fetchone()[0]
    
    def reset_invoice_no(self):
        self.cursor.execute("DELETE FROM sqlite_sequence WHERE name='bills'")
        self.conn.commit()

if __name__ == '__main__':
    # # Execute the SQL script
    # execute_sql_file('database/billing.sql')
    # # Print the schema of the database
    # print_schema()

    # print_all_tables_with_entries('database/sql.db')

    # execute_sql_file('database/test.sql')
    db = DataBase('database/sql.db') 
    # db.execute_sql_query('database/test.sql')
    # db.bootstrap()
    print_all_tables_with_entries('database/sql.db')