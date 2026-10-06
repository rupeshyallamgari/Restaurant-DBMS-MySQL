from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error

app = Flask(
    __name__,
    template_folder="app/templates",
    static_folder="app/static"
)

app.secret_key = "restaurant-dbms-pbl-secret"

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Rupesh0612",
    "database": "restaurant_db",
    "port": 3306
}


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db():
    return mysql.connector.connect(**DB_CONFIG)


def scalar(conn, sql, params=()):
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        row = cur.fetchone()
        return row[0] if row else 0
    finally:
        cur.close()


def fetchall(conn, sql, params=()):
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        cur.close()


def fetchone(conn, sql, params=()):
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(sql, params)
        return cur.fetchone()
    finally:
        cur.close()


def close_db(conn):
    if conn and conn.is_connected():
        conn.close()


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/")
def dashboard():

    conn = get_db()

    try:

        stats = {
            "customers": scalar(
                conn,
                "SELECT COUNT(*) FROM customer"
            ),

            "tables": scalar(
                conn,
                "SELECT COUNT(*) FROM restaurant_table"
            ),

            "available": scalar(
                conn,
                "SELECT COUNT(*) FROM restaurant_table "
                "WHERE status='Available'"
            ),

            "reservations": scalar(
                conn,
                """
                SELECT COUNT(*)
                FROM reservation
                WHERE status IN ('Pending','Confirmed')
                """
            ),

            "orders": scalar(
                conn,
                """
                SELECT COUNT(*)
                FROM food_order
                WHERE status <> 'Cancelled'
                """
            ),

            "kitchen": scalar(
                conn,
                """
                SELECT COUNT(*)
                FROM kitchen_ticket
                WHERE status IN ('Pending','Preparing')
                """
            ),

            "revenue": scalar(
                conn,
                """
                SELECT COALESCE(SUM(amount),0)
                FROM payment
                WHERE status='Successful'
                """
            )
        }

        recent = fetchall(
            conn,
            """
            SELECT
                r.reservation_id,
                c.full_name,
                t.table_number,
                r.reservation_date,
                r.reservation_time,
                r.guest_count,
                r.status
            FROM reservation r
            JOIN customer c
                ON r.customer_id=c.customer_id
            JOIN restaurant_table t
                ON r.table_id=t.table_id
            ORDER BY r.reservation_id DESC
            LIMIT 8
            """
        )

        return render_template(
            "dashboard.html",
            stats=stats,
            recent=recent
        )

    finally:
        close_db(conn)


# ============================================================
# RESTAURANT TABLES
# ============================================================

@app.route("/tables", methods=["GET", "POST"])
def tables():

    conn = get_db()

    try:

        if request.method == "POST":

            cur = None

            try:

                cur = conn.cursor()

                cur.execute(
                    """
                    INSERT INTO restaurant_table
                    (table_number, area_id, capacity, status)
                    VALUES (%s,%s,%s,%s)
                    """,
                    (
                        request.form["table_number"],
                        request.form["area_id"],
                        int(request.form["capacity"]),
                        request.form["status"]
                    )
                )

                conn.commit()

                flash(
                    "Restaurant table added successfully.",
                    "success"
                )

            except Error as e:

                conn.rollback()

                flash(
                    f"Table could not be added: {e}",
                    "error"
                )

            finally:

                if cur:
                    cur.close()

            return redirect(url_for("tables"))

        rows = fetchall(
            conn,
            """
            SELECT
                t.*,
                a.area_name
            FROM restaurant_table t
            JOIN dining_area a
                ON t.area_id=a.area_id
            ORDER BY t.table_number
            """
        )

        areas = fetchall(
            conn,
            """
            SELECT *
            FROM dining_area
            ORDER BY area_name
            """
        )

        return render_template(
            "tables.html",
            rows=rows,
            areas=areas
        )

    finally:
        close_db(conn)


# ============================================================
# CUSTOMERS
# ============================================================

@app.route("/customers", methods=["GET", "POST"])
def customers():

    conn = get_db()

    try:

        if request.method == "POST":

            cur = None

            try:

                cur = conn.cursor()

                cur.execute(
                    """
                    INSERT INTO customer
                    (full_name, phone, email, address)
                    VALUES (%s,%s,%s,%s)
                    """,
                    (
                        request.form["full_name"],
                        request.form["phone"],
                        request.form.get("email") or None,
                        request.form.get("address") or None
                    )
                )

                conn.commit()

                flash(
                    "Customer added successfully.",
                    "success"
                )

            except Error as e:

                conn.rollback()

                flash(
                    f"Customer could not be added: {e}",
                    "error"
                )

            finally:

                if cur:
                    cur.close()

            return redirect(url_for("customers"))

        rows = fetchall(
            conn,
            """
            SELECT *
            FROM customer
            ORDER BY customer_id DESC
            """
        )

        return render_template(
            "customers.html",
            rows=rows
        )

    finally:
        close_db(conn)


# ============================================================
# RESERVATIONS
# ============================================================

@app.route("/reservations", methods=["GET", "POST"])
def reservations():

    conn = get_db()

    try:

        if request.method == "POST":

            table_id = int(request.form["table_id"])
            guest_count = int(request.form["guest_count"])

            table = fetchone(
                conn,
                """
                SELECT capacity
                FROM restaurant_table
                WHERE table_id=%s
                """,
                (table_id,)
            )

            if not table:

                flash(
                    "Selected table does not exist.",
                    "error"
                )

                return redirect(url_for("reservations"))

            if guest_count > table["capacity"]:

                flash(
                    "Guest count exceeds the selected table capacity.",
                    "error"
                )

                return redirect(url_for("reservations"))

            conflict = scalar(
                conn,
                """
                SELECT COUNT(*)
                FROM reservation
                WHERE table_id=%s
                AND reservation_date=%s
                AND reservation_time=%s
                AND status IN ('Pending','Confirmed')
                """,
                (
                    table_id,
                    request.form["reservation_date"],
                    request.form["reservation_time"]
                )
            )

            if conflict:

                flash(
                    "This table is already reserved for that date and time.",
                    "error"
                )

                return redirect(url_for("reservations"))

            cur = None

            try:

                cur = conn.cursor()

                cur.execute(
                    """
                    INSERT INTO reservation
                    (
                        customer_id,
                        table_id,
                        reservation_date,
                        reservation_time,
                        guest_count,
                        status
                    )
                    VALUES (%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        request.form["customer_id"],
                        table_id,
                        request.form["reservation_date"],
                        request.form["reservation_time"],
                        guest_count,
                        request.form["status"]
                    )
                )

                if request.form["status"] == "Confirmed":

                    cur.execute(
                        """
                        UPDATE restaurant_table
                        SET status='Reserved'
                        WHERE table_id=%s
                        """,
                        (table_id,)
                    )

                conn.commit()

                flash(
                    "Reservation created successfully.",
                    "success"
                )

            except Error as e:

                conn.rollback()

                flash(
                    f"Reservation could not be created: {e}",
                    "error"
                )

            finally:

                if cur:
                    cur.close()

            return redirect(url_for("reservations"))

        rows = fetchall(
            conn,
            """
            SELECT
                r.*,
                c.full_name,
                t.table_number
            FROM reservation r
            JOIN customer c
                ON r.customer_id=c.customer_id
            JOIN restaurant_table t
                ON r.table_id=t.table_id
            ORDER BY r.reservation_id DESC
            """
        )

        customers_list = fetchall(
            conn,
            """
            SELECT *
            FROM customer
            ORDER BY full_name
            """
        )

        tables_list = fetchall(
            conn,
            """
            SELECT *
            FROM restaurant_table
            WHERE status <> 'Maintenance'
            ORDER BY table_number
            """
        )

        return render_template(
            "reservations.html",
            rows=rows,
            customers=customers_list,
            tables=tables_list
        )

    finally:
        close_db(conn)


# ============================================================
# MENU
# ============================================================

@app.route("/menu", methods=["GET", "POST"])
def menu():

    conn = get_db()

    try:

        if request.method == "POST":

            cur = None

            try:

                cur = conn.cursor()

                cur.execute(
                    """
                    INSERT INTO menu_item
                    (
                        category_id,
                        item_name,
                        description,
                        price,
                        availability
                    )
                    VALUES (%s,%s,%s,%s,%s)
                    """,
                    (
                        request.form["category_id"],
                        request.form["item_name"],
                        request.form.get("description") or None,
                        float(request.form["price"]),
                        request.form["availability"]
                    )
                )

                conn.commit()

                flash(
                    "Menu item added.",
                    "success"
                )

            except Error as e:

                conn.rollback()

                flash(
                    f"Menu item could not be added: {e}",
                    "error"
                )

            finally:

                if cur:
                    cur.close()

            return redirect(url_for("menu"))

        rows = fetchall(
            conn,
            """
            SELECT
                m.*,
                c.category_name
            FROM menu_item m
            JOIN menu_category c
                ON m.category_id=c.category_id
            ORDER BY c.category_name,m.item_name
            """
        )

        categories = fetchall(
            conn,
            """
            SELECT *
            FROM menu_category
            ORDER BY category_name
            """
        )

        return render_template(
            "menu.html",
            rows=rows,
            categories=categories
        )

    finally:
        close_db(conn)


# ============================================================
# FOOD ORDERS
# ============================================================

@app.route("/orders", methods=["GET", "POST"])
def orders():

    conn = get_db()

    try:

        if request.method == "POST":

            customer_id = request.form.get("customer_id") or None
            table_id = int(request.form["table_id"])
            waiter_id = request.form.get("waiter_id") or None
            item_id = int(request.form["item_id"])
            qty = int(request.form["quantity"])

            item = fetchone(
                conn,
                """
                SELECT price, availability
                FROM menu_item
                WHERE item_id=%s
                """,
                (item_id,)
            )

            if not item:

                flash(
                    "Selected menu item does not exist.",
                    "error"
                )

                return redirect(url_for("orders"))

            if item["availability"] != "Available":

                flash(
                    "Selected menu item is unavailable.",
                    "error"
                )

                return redirect(url_for("orders"))

            if qty <= 0:

                flash(
                    "Quantity must be positive.",
                    "error"
                )

                return redirect(url_for("orders"))

            cur = None

            try:

                cur = conn.cursor()

                cur.execute(
                    """
                    INSERT INTO food_order
                    (
                        customer_id,
                        table_id,
                        waiter_id,
                        status
                    )
                    VALUES (%s,%s,%s,'Placed')
                    """,
                    (
                        customer_id,
                        table_id,
                        waiter_id
                    )
                )

                order_id = cur.lastrowid

                cur.execute(
                    """
                    INSERT INTO order_item
                    (
                        order_id,
                        item_id,
                        quantity,
                        unit_price
                    )
                    VALUES (%s,%s,%s,%s)
                    """,
                    (
                        order_id,
                        item_id,
                        qty,
                        item["price"]
                    )
                )

                cur.execute(
                    """
                    INSERT INTO kitchen_ticket
                    (order_id,status)
                    VALUES (%s,'Pending')
                    """,
                    (order_id,)
                )

                cur.execute(
                    """
                    UPDATE restaurant_table
                    SET status='Occupied'
                    WHERE table_id=%s
                    """,
                    (table_id,)
                )

                conn.commit()

                flash(
                    f"Order #{order_id} created and sent to kitchen.",
                    "success"
                )

            except Error as e:

                conn.rollback()

                flash(
                    f"Order could not be created: {e}",
                    "error"
                )

            finally:

                if cur:
                    cur.close()

            return redirect(url_for("orders"))

        rows = fetchall(
            conn,
            """
            SELECT
                o.*,
                c.full_name,
                t.table_number,
                w.waiter_name,
                COALESCE(
                    SUM(oi.quantity * oi.unit_price),
                    0
                ) AS subtotal
            FROM food_order o
            LEFT JOIN customer c
                ON o.customer_id=c.customer_id
            JOIN restaurant_table t
                ON o.table_id=t.table_id
            LEFT JOIN waiter w
                ON o.waiter_id=w.waiter_id
            LEFT JOIN order_item oi
                ON o.order_id=oi.order_id
            GROUP BY
                o.order_id,
                c.full_name,
                t.table_number,
                w.waiter_name
            ORDER BY o.order_id DESC
            """
        )

        customers_list = fetchall(
            conn,
            """
            SELECT *
            FROM customer
            ORDER BY full_name
            """
        )

        tables_list = fetchall(
            conn,
            """
            SELECT *
            FROM restaurant_table
            WHERE status <> 'Maintenance'
            ORDER BY table_number
            """
        )

        waiters = fetchall(
            conn,
            """
            SELECT *
            FROM waiter
            WHERE status='Active'
            ORDER BY waiter_name
            """
        )

        items = fetchall(
            conn,
            """
            SELECT *
            FROM menu_item
            WHERE availability='Available'
            ORDER BY item_name
            """
        )

        return render_template(
            "orders.html",
            rows=rows,
            customers=customers_list,
            tables=tables_list,
            waiters=waiters,
            items=items
        )

    finally:
        close_db(conn)


# ============================================================
# KITCHEN
# ============================================================

@app.route("/kitchen")
def kitchen():

    conn = get_db()

    try:

        rows = fetchall(
            conn,
            """
            SELECT
                k.*,
                o.table_id,
                t.table_number,
                o.status AS order_status
            FROM kitchen_ticket k
            JOIN food_order o
                ON k.order_id=o.order_id
            JOIN restaurant_table t
                ON o.table_id=t.table_id
            ORDER BY k.ticket_id DESC
            """
        )

        return render_template(
            "kitchen.html",
            rows=rows
        )

    finally:
        close_db(conn)


@app.post("/kitchen/<int:ticket_id>")
def update_kitchen(ticket_id):

    status = request.form["status"]

    conn = get_db()

    try:

        cur = conn.cursor()

        cur.execute(
            """
            UPDATE kitchen_ticket
            SET status=%s
            WHERE ticket_id=%s
            """,
            (
                status,
                ticket_id
            )
        )

        cur.execute(
            """
            SELECT order_id
            FROM kitchen_ticket
            WHERE ticket_id=%s
            """,
            (ticket_id,)
        )

        row = cur.fetchone()

        if row:

            cur.execute(
                """
                UPDATE food_order
                SET status=%s
                WHERE order_id=%s
                """,
                (
                    status,
                    row[0]
                )
            )

        conn.commit()

        flash(
            "Kitchen status updated.",
            "success"
        )

        cur.close()

    except Error as e:

        conn.rollback()

        flash(
            f"Kitchen update failed: {e}",
            "error"
        )

    finally:

        close_db(conn)

    return redirect(url_for("kitchen"))


# ============================================================
# BILLING
# ============================================================

@app.route("/billing", methods=["GET", "POST"])
def billing():

    conn = get_db()

    try:

        if request.method == "POST":

            order_id = int(request.form["order_id"])
            discount_id = request.form.get("discount_id") or None

            order = fetchone(
                conn,
                """
                SELECT
                    COALESCE(
                        SUM(quantity * unit_price),
                        0
                    ) AS subtotal
                FROM order_item
                WHERE order_id=%s
                """,
                (order_id,)
            )

            subtotal = float(order["subtotal"])

            discount_amount = 0.0

            if discount_id:

                discount = fetchone(
                    conn,
                    """
                    SELECT discount_percent
                    FROM discount
                    WHERE discount_id=%s
                    AND active=1
                    """,
                    (discount_id,)
                )

                if discount:

                    discount_amount = (
                        subtotal
                        * float(discount["discount_percent"])
                        / 100
                    )

            taxable = subtotal - discount_amount

            tax = round(
                taxable * 0.05,
                2
            )

            total = round(
                taxable + tax,
                2
            )

            cur = None

            try:

                cur = conn.cursor()

                cur.execute(
                    """
                    INSERT INTO bill
                    (
                        order_id,
                        subtotal,
                        discount_amount,
                        tax,
                        total_amount,
                        status,
                        discount_id
                    )
                    VALUES (%s,%s,%s,%s,%s,'Open',%s)
                    """,
                    (
                        order_id,
                        subtotal,
                        discount_amount,
                        tax,
                        total,
                        discount_id
                    )
                )

                conn.commit()

                flash(
                    f"Bill generated. Total: ₹{total:.2f}",
                    "success"
                )

            except Error as e:

                conn.rollback()

                flash(
                    f"Bill could not be generated: {e}",
                    "error"
                )

            finally:

                if cur:
                    cur.close()

            return redirect(url_for("billing"))

        bills = fetchall(
            conn,
            """
            SELECT
                b.*,
                o.order_id,
                t.table_number,

                COALESCE(
                    (
                        SELECT SUM(p.amount)
                        FROM payment p
                        WHERE p.bill_id=b.bill_id
                        AND p.status='Successful'
                    ),
                    0
                ) AS paid

            FROM bill b

            JOIN food_order o
                ON b.order_id=o.order_id

            JOIN restaurant_table t
                ON o.table_id=t.table_id

            ORDER BY b.bill_id DESC
            """
        )

        orders_without_bill = fetchall(
            conn,
            """
            SELECT
                o.order_id,
                t.table_number

            FROM food_order o

            JOIN restaurant_table t
                ON o.table_id=t.table_id

            WHERE o.status <> 'Cancelled'

            AND NOT EXISTS
            (
                SELECT 1
                FROM bill b
                WHERE b.order_id=o.order_id
            )

            ORDER BY o.order_id DESC
            """
        )

        discounts = fetchall(
            conn,
            """
            SELECT *
            FROM discount
            WHERE active=1
            ORDER BY discount_code
            """
        )

        return render_template(
            "billing.html",
            bills=bills,
            orders=orders_without_bill,
            discounts=discounts
        )

    finally:
        close_db(conn)


# ============================================================
# PAYMENT
# ============================================================

@app.post("/payment/<int:bill_id>")
def payment(bill_id):

    amount = float(
        request.form["amount"]
    )

    method = request.form["payment_method"]

    conn = get_db()

    try:

        bill = fetchone(
            conn,
            """
            SELECT
                b.total_amount,

                COALESCE(
                    (
                        SELECT SUM(p.amount)
                        FROM payment p
                        WHERE p.bill_id=b.bill_id
                        AND p.status='Successful'
                    ),
                    0
                ) AS paid

            FROM bill b
            WHERE b.bill_id=%s
            """,
            (bill_id,)
        )

        if not bill:

            flash(
                "Bill not found.",
                "error"
            )

        elif (
            amount <= 0
            or amount >
            float(
                bill["total_amount"]
                - bill["paid"]
            ) + 0.001
        ):

            flash(
                "Payment exceeds the outstanding balance or is invalid.",
                "error"
            )

        else:

            cur = conn.cursor()

            cur.execute(
                """
                INSERT INTO payment
                (
                    bill_id,
                    amount,
                    payment_method,
                    status
                )
                VALUES (%s,%s,%s,'Successful')
                """,
                (
                    bill_id,
                    amount,
                    method
                )
            )

            new_paid = (
                float(bill["paid"])
                + amount
            )

            if (
                new_paid
                >= float(bill["total_amount"])
                - 0.001
            ):
                status = "Paid"
            else:
                status = "Partially Paid"

            cur.execute(
                """
                UPDATE bill
                SET status=%s
                WHERE bill_id=%s
                """,
                (
                    status,
                    bill_id
                )
            )

            conn.commit()

            cur.close()

            flash(
                "Payment recorded successfully.",
                "success"
            )

    except Error as e:

        conn.rollback()

        flash(
            f"Payment failed: {e}",
            "error"
        )

    finally:

        close_db(conn)

    return redirect(url_for("billing"))


# ============================================================
# REPORTS
# ============================================================

@app.route("/reports")
def reports():

    conn = get_db()

    try:

        item_sales = fetchall(
            conn,
            """
            SELECT
                mi.item_name,
                SUM(oi.quantity) AS quantity_sold,
                SUM(
                    oi.quantity * oi.unit_price
                ) AS sales_value

            FROM order_item oi

            JOIN menu_item mi
                ON oi.item_id=mi.item_id

            JOIN food_order o
                ON oi.order_id=o.order_id

            WHERE o.status <> 'Cancelled'

            GROUP BY
                mi.item_id,
                mi.item_name

            ORDER BY quantity_sold DESC
            """
        )

        waiter_sales = fetchall(
            conn,
            """
            SELECT
                w.waiter_name,
                COUNT(o.order_id) AS orders_handled,
                COALESCE(
                    SUM(b.total_amount),
                    0
                ) AS billed_value

            FROM waiter w

            LEFT JOIN food_order o
                ON w.waiter_id=o.waiter_id

            LEFT JOIN bill b
                ON o.order_id=b.order_id

            GROUP BY
                w.waiter_id,
                w.waiter_name

            ORDER BY billed_value DESC
            """
        )

        revenue = scalar(
            conn,
            """
            SELECT COALESCE(SUM(amount),0)
            FROM payment
            WHERE status='Successful'
            """
        )

        reservations_summary = fetchall(
            conn,
            """
            SELECT
                status,
                COUNT(*) AS count

            FROM reservation

            GROUP BY status
            """
        )

        return render_template(
            "reports.html",
            item_sales=item_sales,
            waiter_sales=waiter_sales,
            revenue=revenue,
            reservations=reservations_summary
        )

    finally:
        close_db(conn)


# ============================================================
# DATABASE VALIDATION
# ============================================================

@app.route("/database-validation")
def validation():

    conn = get_db()

    try:

        checks = []

        checks.append(
            (
                "Invalid table capacities",
                scalar(
                    conn,
                    """
                    SELECT COUNT(*)
                    FROM restaurant_table
                    WHERE capacity<=0
                    """
                )
            )
        )

        checks.append(
            (
                "Invalid menu prices",
                scalar(
                    conn,
                    """
                    SELECT COUNT(*)
                    FROM menu_item
                    WHERE price<=0
                    """
                )
            )
        )

        checks.append(
            (
                "Invalid order quantities",
                scalar(
                    conn,
                    """
                    SELECT COUNT(*)
                    FROM order_item
                    WHERE quantity<=0
                    """
                )
            )
        )

        checks.append(
            (
                "Negative bills",
                scalar(
                    conn,
                    """
                    SELECT COUNT(*)
                    FROM bill
                    WHERE total_amount<0
                    """
                )
            )
        )

        checks.append(
            (
                "Payments above bill totals",
                scalar(
                    conn,
                    """
                    SELECT COUNT(*)
                    FROM
                    (
                        SELECT
                            b.bill_id

                        FROM bill b

                        LEFT JOIN payment p
                            ON b.bill_id=p.bill_id
                            AND p.status='Successful'

                        GROUP BY
                            b.bill_id,
                            b.total_amount

                        HAVING
                            COALESCE(
                                SUM(p.amount),
                                0
                            )
                            >
                            b.total_amount + 0.001

                    ) AS x
                    """
                )
            )
        )

        return render_template(
            "validation.html",
            checks=checks
        )

    finally:

        close_db(conn)


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print(" RESTAURANT DBMS - MYSQL VERSION")
    print("=" * 60)
    print("Database: restaurant_db")
    print("Server: http://127.0.0.1:5000")
    print("=" * 60)

    try:

        test = get_db()

        print("MySQL connection: SUCCESS")

        close_db(test)

    except Error as e:

        print("MySQL connection FAILED:", e)

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )