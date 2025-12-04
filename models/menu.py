"""
Business logic related to menu items and recipes.
"""
from sqlite3 import Connection
from typing import List, Dict, Any


def get_menu_items(conn: Connection, include_inactive: bool = False) -> List[Dict[str, Any]]:
    """Return all menu items as a list of dicts."""
    cursor = conn.cursor()
    if include_inactive:
        cursor.execute("SELECT * FROM menu_items")
    else:
        cursor.execute("SELECT * FROM menu_items WHERE active = 1")
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def add_menu_item(
    conn: Connection,
    name: str,
    category: str,
    price: float,
    image_path: str | None = None,
) -> int:
    """Insert a new menu item and return its ID."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO menu_items (name, category, price, image_path) VALUES (?, ?, ?, ?)",
        (name, category, price, image_path),
    )
    conn.commit()
    return cursor.lastrowid
