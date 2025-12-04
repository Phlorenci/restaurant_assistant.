"""
Business logic related to sales_log and income summaries.
"""

from sqlite3 import Connection
from typing import List, Dict, Any


def record_sales(
    conn: Connection,
    date: str,
    menu_item_id: int,
    dine_in_qty: int,
    delivery_qty: int,
) -> None:
    """
    Insert a single sales row into sales_log.

    - date: 'YYYY-MM-DD'
    - menu_item_id: ID from menu_items table
    - dine_in_qty / delivery_qty: how many sold for each channel
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO sales_log (date, menu_item_id, dine_in_qty, delivery_qty)
        VALUES (?, ?, ?, ?)
        """,
        (date, menu_item_id, dine_in_qty, delivery_qty),
    )
    conn.commit()


def record_sales_batch(conn: Connection, date: str, sales_rows: List[Dict[str, int]]) -> None:
    """
    Insert multiple sales rows at once for the same date.

    sales_rows is a list of dicts like:
        {
            "menu_item_id": 1,
            "dine_in_qty": 10,
            "delivery_qty": 5,
        }

    This is useful when we submit a form with many items.
    """
    cursor = conn.cursor()
    for row in sales_rows:
        menu_item_id = row["menu_item_id"]
        dine_in_qty = row.get("dine_in_qty", 0)
        delivery_qty = row.get("delivery_qty", 0)

        # Ignore rows where everything is 0 (no sales for that item)
        if dine_in_qty == 0 and delivery_qty == 0:
            continue

        cursor.execute(
            """
            INSERT INTO sales_log (date, menu_item_id, dine_in_qty, delivery_qty)
            VALUES (?, ?, ?, ?)
            """,
            (date, menu_item_id, dine_in_qty, delivery_qty),
        )

    conn.commit()


def get_daily_income(conn: Connection, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Return income per day between two dates (inclusive).

    Each result dict has:
        {
            "date": "YYYY-MM-DD",
            "total_income": float,
            "dine_in_income": float,
            "delivery_income": float,
        }
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            s.date AS date,
            SUM((s.dine_in_qty + s.delivery_qty) * m.price) AS total_income,
            SUM(s.dine_in_qty * m.price) AS dine_in_income,
            SUM(s.delivery_qty * m.price) AS delivery_income
        FROM sales_log s
        JOIN menu_items m ON s.menu_item_id = m.id
        WHERE s.date BETWEEN ? AND ?
        GROUP BY s.date
        ORDER BY s.date
        """,
        (start_date, end_date),
    )
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def get_top_menu_items(
    conn: Connection,
    start_date: str,
    end_date: str,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Return top-selling menu items in a date range.

    Each dict:
        {
            "menu_item_id": int,
            "name": str,
            "total_qty": int,
            "total_revenue": float,
        }
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            m.id AS menu_item_id,
            m.name AS name,
            SUM(s.dine_in_qty + s.delivery_qty) AS total_qty,
            SUM((s.dine_in_qty + s.delivery_qty) * m.price) AS total_revenue
        FROM sales_log s
        JOIN menu_items m ON s.menu_item_id = m.id
        WHERE s.date BETWEEN ? AND ?
        GROUP BY m.id, m.name
        ORDER BY total_qty DESC
        LIMIT ?
        """,
        (start_date, end_date, limit),
    )
    rows = cursor.fetchall()
    return [dict(row) for row in rows]
