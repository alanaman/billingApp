DROP TABLE IF EXISTS product;
DROP TABLE IF EXISTS curr_bill;
DROP TABLE IF EXISTS bills;
DROP TABLE IF EXISTS bill_items;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS roles;

create table roles (
    role_name TEXT PRIMARY KEY
);

create table users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    role_name TEXT NOT NULL,
    FOREIGN KEY (role_name) REFERENCES roles(role_name)
);

--create product table if not exists
CREATE TABLE product (
    p_id INTEGER PRIMARY KEY AUTOINCREMENT,
    p_name TEXT NOT NULL,
    HSN TEXT NOT NULL,
    price REAL NOT NULL,
    stock REAL NOT NULL,
    unit TEXT NOT NULL,
    tax_perc REAL NOT NULL,
    p_desc TEXT
) STRICT;

CREATE TABLE curr_bill (
    p_id INTEGER,
    p_name TEXT NOT NULL,
    HSN TEXT NOT NULL,
    unit_price REAL NOT NULL,
    quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    tax_perc REAL NOT NULL,
    PRIMARY KEY (p_id, p_name)
) STRICT;

CREATE TABLE bills (
    bill_id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Unique bill ID
    creator TEXT NOT NULL,  -- Username of the user who created the bill
    timestamp DATETIME DEFAULT (datetime('now','localtime')) -- Auto-generated timestamp
);

CREATE TABLE bill_items (
    bill_id INTEGER,  -- Foreign key referring to bills
    p_id INTEGER,  
    p_name TEXT NOT NULL,
    HSN TEXT NOT NULL,
    unit_price REAL NOT NULL,
    quantity REAL NOT NULL,  
    unit TEXT NOT NULL,  
    tax_perc REAL NOT NULL,
    PRIMARY KEY (bill_id, p_id, p_name),  -- Each product in a bill is unique
    FOREIGN KEY (bill_id) REFERENCES bills(bill_id) ON DELETE CASCADE
);

INSERT INTO roles (role_name) VALUES ('admin');
INSERT INTO roles (role_name) VALUES ('user');
-- INSERT INTO product (id, p_name, price, stock, p_desc) VALUES (100, 'Product 1', 100.00, 10, 'Product 1 Description');
-- INSERT INTO product (p_id, p_name, price, stock, p_desc) VALUES (100, 'Product 1', 100.00, 10, 'Product 1 Description');
-- INSERT INTO product (p_name, price, stock, p_desc) VALUES ('Product 1', 100.00, 10, 'Product 1 Description');
-- INSERT INTO product (p_id, p_name, price, stock, p_desc) VALUES (10, 'Product 1', 100.00, 10, 'Product 1 Description');
-- INSERT INTO product (p_name, price, stock, p_desc) VALUES ('Product 1', 100.00, 10, 'Product 1 Description');
