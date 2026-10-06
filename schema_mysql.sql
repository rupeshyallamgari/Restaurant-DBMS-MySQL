-- ============================================================
-- RESTAURANT DBMS - MYSQL DATABASE SCHEMA
-- ============================================================

CREATE DATABASE IF NOT EXISTS restaurant_db;
USE restaurant_db;

-- 1. Dining Area
CREATE TABLE IF NOT EXISTS dining_area (
    area_id INT AUTO_INCREMENT PRIMARY KEY,
    area_name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255)
) ENGINE=InnoDB;

-- 2. Restaurant Table
CREATE TABLE IF NOT EXISTS restaurant_table (
    table_id INT AUTO_INCREMENT PRIMARY KEY,
    table_number VARCHAR(20) NOT NULL UNIQUE,
    area_id INT NOT NULL,
    capacity INT NOT NULL,
    status ENUM('Available', 'Reserved', 'Occupied', 'Maintenance') DEFAULT 'Available',
    FOREIGN KEY (area_id) REFERENCES dining_area(area_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 3. Customer
CREATE TABLE IF NOT EXISTS customer (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(100),
    address VARCHAR(255)
) ENGINE=InnoDB;

-- 4. Reservation
CREATE TABLE IF NOT EXISTS reservation (
    reservation_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    table_id INT NOT NULL,
    reservation_date DATE NOT NULL,
    reservation_time TIME NOT NULL,
    guest_count INT NOT NULL,
    status ENUM('Pending', 'Confirmed', 'Cancelled', 'Completed') DEFAULT 'Pending',
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (table_id) REFERENCES restaurant_table(table_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 5. Menu Category
CREATE TABLE IF NOT EXISTS menu_category (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL UNIQUE
) ENGINE=InnoDB;

-- 6. Menu Item
CREATE TABLE IF NOT EXISTS menu_item (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL,
    item_name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    price DECIMAL(10,2) NOT NULL,
    availability ENUM('Available', 'Unavailable') DEFAULT 'Available',
    FOREIGN KEY (category_id) REFERENCES menu_category(category_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 7. Waiter
CREATE TABLE IF NOT EXISTS waiter (
    waiter_id INT AUTO_INCREMENT PRIMARY KEY,
    waiter_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL UNIQUE,
    shift ENUM('Morning', 'Evening', 'Night') DEFAULT 'Morning',
    status ENUM('Active', 'Inactive') DEFAULT 'Active'
) ENGINE=InnoDB;

-- 8. Food Order
CREATE TABLE IF NOT EXISTS food_order (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    table_id INT NOT NULL,
    waiter_id INT,
    status ENUM('Placed', 'Preparing', 'Ready', 'Served', 'Cancelled') DEFAULT 'Placed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON DELETE SET NULL,
    FOREIGN KEY (table_id) REFERENCES restaurant_table(table_id) ON DELETE CASCADE,
    FOREIGN KEY (waiter_id) REFERENCES waiter(waiter_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 9. Order Item
CREATE TABLE IF NOT EXISTS order_item (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    item_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES food_order(order_id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES menu_item(item_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 10. Kitchen Ticket
CREATE TABLE IF NOT EXISTS kitchen_ticket (
    ticket_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL UNIQUE,
    status ENUM('Pending', 'Preparing', 'Ready', 'Served') DEFAULT 'Pending',
    started_at DATETIME,
    completed_at DATETIME,
    FOREIGN KEY (order_id) REFERENCES food_order(order_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 11. Discount
CREATE TABLE IF NOT EXISTS discount (
    discount_id INT AUTO_INCREMENT PRIMARY KEY,
    discount_code VARCHAR(30) NOT NULL UNIQUE,
    description VARCHAR(255),
    discount_percent DECIMAL(5,2) NOT NULL,
    authorized_by VARCHAR(100),
    active TINYINT(1) DEFAULT 1
) ENGINE=InnoDB;

-- 12. Bill
CREATE TABLE IF NOT EXISTS bill (
    bill_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL UNIQUE,
    subtotal DECIMAL(10,2) NOT NULL,
    discount_amount DECIMAL(10,2) DEFAULT 0.00,
    tax DECIMAL(10,2) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status ENUM('Open', 'Partially Paid', 'Paid') DEFAULT 'Open',
    discount_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES food_order(order_id) ON DELETE CASCADE,
    FOREIGN KEY (discount_id) REFERENCES discount(discount_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 13. Payment
CREATE TABLE IF NOT EXISTS payment (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    bill_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method ENUM('Cash', 'Card', 'UPI') NOT NULL,
    status ENUM('Successful', 'Failed') DEFAULT 'Successful',
    paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bill_id) REFERENCES bill(bill_id) ON DELETE CASCADE
) ENGINE=InnoDB;