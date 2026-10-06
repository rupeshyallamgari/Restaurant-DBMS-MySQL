USE restaurant_db;

SET FOREIGN_KEY_CHECKS = 0;

DELETE FROM payment;
DELETE FROM bill;
DELETE FROM discount;
DELETE FROM kitchen_ticket;
DELETE FROM order_item;
DELETE FROM food_order;
DELETE FROM waiter;
DELETE FROM menu_item;
DELETE FROM menu_category;
DELETE FROM reservation;
DELETE FROM customer;
DELETE FROM restaurant_table;
DELETE FROM dining_area;

SET FOREIGN_KEY_CHECKS = 1;

INSERT INTO dining_area(area_name, description) VALUES
('Indoor','Air-conditioned indoor dining'),
('Outdoor','Open-air garden seating'),
('Family Zone','Family and group seating');

INSERT INTO restaurant_table(table_number,area_id,capacity,status) VALUES
('T01',1,2,'Available'),
('T02',1,4,'Available'),
('T03',1,6,'Available'),
('T04',2,4,'Available'),
('T05',2,6,'Reserved'),
('T06',3,8,'Available'),
('T07',3,4,'Occupied'),
('T08',3,10,'Available');

INSERT INTO customer(full_name,phone,email,address) VALUES
('Arjun Reddy','9876500001','arjun@example.com','Hyderabad'),
('Sneha Rao','9876500002','sneha@example.com','Warangal'),
('Rahul Kumar','9876500003','rahul@example.com','Vijayawada'),
('Ananya Sharma','9876500004','ananya@example.com','Bengaluru'),
('Vikram Singh','9876500005','vikram@example.com','Chennai');

INSERT INTO menu_category(category_name) VALUES
('Starters'),('Main Course'),('Biryani'),('Beverages'),('Desserts');

INSERT INTO menu_item(category_id,item_name,description,price,availability) VALUES
(1,'Paneer Tikka','Grilled cottage cheese',220,'Available'),
(1,'Chicken 65','Spicy fried chicken',260,'Available'),
(2,'Paneer Butter Masala','Creamy paneer curry',240,'Available'),
(2,'Chicken Curry','Traditional chicken curry',280,'Available'),
(3,'Chicken Biryani','Hyderabadi dum biryani',320,'Available'),
(3,'Veg Biryani','Vegetable dum biryani',220,'Available'),
(4,'Fresh Lime Soda','Chilled lime drink',90,'Available'),
(4,'Mango Lassi','Mango yogurt drink',120,'Available'),
(5,'Gulab Jamun','Two pieces',100,'Available'),
(5,'Brownie','Chocolate brownie',150,'Unavailable');

INSERT INTO waiter(waiter_name,phone,shift,status) VALUES
('Kiran','9000000011','Morning','Active'),
('Pooja','9000000012','Evening','Active'),
('Manoj','9000000013','Evening','Active'),
('Suresh','9000000014','Night','Active');

INSERT INTO reservation(customer_id,table_id,reservation_date,reservation_time,guest_count,status) VALUES
(1,2,CURDATE() + INTERVAL 1 DAY,'19:30:00',4,'Confirmed'),
(2,4,CURDATE() + INTERVAL 1 DAY,'20:00:00',3,'Confirmed'),
(3,6,CURDATE() + INTERVAL 2 DAY,'13:00:00',6,'Pending');

INSERT INTO food_order(customer_id,table_id,waiter_id,status) VALUES
(4,7,2,'Served'),
(1,3,1,'Preparing');

INSERT INTO order_item(order_id,item_id,quantity,unit_price) VALUES
(1,5,2,320),
(1,7,2,90),
(1,9,2,100),
(2,2,1,260),
(2,5,1,320);

INSERT INTO kitchen_ticket(order_id,status,started_at,completed_at) VALUES
(1,'Served',NOW() - INTERVAL 1 HOUR,NOW() - INTERVAL 20 MINUTE),
(2,'Preparing',NOW() - INTERVAL 10 MINUTE,NULL);

INSERT INTO discount(discount_code,description,discount_percent,authorized_by,active) VALUES
('WELCOME10','New customer discount',10,'Manager',1),
('FAMILY15','Family dining offer',15,'Manager',1),
('STUDENT5','Student discount',5,'Supervisor',1);

INSERT INTO bill(order_id,subtotal,discount_amount,tax,total_amount,status,discount_id) VALUES
(1,1100,110,99,1089,'Paid',1);

INSERT INTO payment(bill_id,amount,payment_method,status) VALUES
(1,1089,'UPI','Successful');
