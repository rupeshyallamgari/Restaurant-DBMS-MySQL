# Restaurant DBMS - Complete MySQL Version

This version is converted from the original working SQLite project.

## Technology
- Python 3
- Flask
- MySQL 8.x
- HTML5 / CSS3
- SQL

## Database
Database name: `restaurant_db`

The MySQL database contains the complete original 13-table structure:
1. dining_area
2. restaurant_table
3. customer
4. reservation
5. menu_category
6. menu_item
7. waiter
8. food_order
9. order_item
10. kitchen_ticket
11. discount
12. bill
13. payment

## Setup

1. Open MySQL Workbench.
2. Open `schema_mysql.sql` and run it.
3. Open `seed_mysql.sql` and run it.
4. Copy the original project's `app/` folder (templates and static) into this project folder.
5. Open `app.py`.
6. Change `YOUR_MYSQL_PASSWORD` to your MySQL root password.
7. Install the connector:

```cmd
python -m pip install mysql-connector-python
```

8. Run:

```cmd
python app.py
```

9. Open:

http://127.0.0.1:5000

## Important
The HTML templates from the original SQLite project should be kept. This `app.py` uses the same variable names and route structure as the original project, while replacing SQLite operations with MySQL operations.
