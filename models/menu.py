"""
Business logic related to menu items and (later) recipes.

This module handles CRUD operations for the menu_items table:
- List all menu items
- Get a single menu item
- Add a new menu item
- Update an existing menu item
- Activate / deactivate a menu item (soft delete)
"""

from sqlite3 import Connection
from typing import List, Dict, Any, Optional


def get_menu_items(conn: Connection, include_inactive: bool = False) -> List[Dict[str, Any]]:
    """
    Return all menu items as a list of dicts.

    If include_inactive is False (default),
    only return rows where active = 1 (currently used in the restaurant).
    """
    cursor = conn.cursor()

    if include_inactive:
        # Show everything (even old / inactive items)
        cursor.execute("SELECT * FROM menu_items ORDER BY id")
    else:
        # Show only active items (for income recording etc.)
        cursor.execute("SELECT * FROM menu_items WHERE active = 1 ORDER BY id")

    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def get_menu_item(conn: Connection, item_id: int) -> Optional[Dict[str, Any]]:
    """
    Return a single menu item as a dict, or None if not found.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM menu_items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def add_menu_item(
    conn: Connection,
    name: str,
    category: str,
    price: float,
    image_path: str | None = None,
) -> int:
    """
    Insert a new menu item and return its ID.

    - name: name of the dish/drink (e.g. "Margherita Pizza")
    - category: group (e.g. "pizza", "drink")
    - price: price per item (float, in ₩)
    - image_path: optional path to picture (we'll use later)
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO menu_items (name, category, price, image_path)
        VALUES (?, ?, ?, ?)
        """,
        (name, category, price, image_path),
    )
    conn.commit()
    return cursor.lastrowid


def update_menu_item(
    conn: Connection,
    item_id: int,
    name: str,
    category: str,
    price: float,
    image_path: str | None = None,
) -> None:
    """
    Update an existing menu item.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE menu_items
        SET name = ?,
            category = ?,
            price = ?,
            image_path = ?
        WHERE id = ?
        """,
        (name, category, price, image_path, item_id),
    )
    conn.commit()


def set_menu_item_active(conn: Connection, item_id: int, active: bool) -> None:
    """
    Activate or deactivate a menu item (soft delete instead of hard delete).

    - active=True  -> active = 1 (visible / usable)
    - active=False -> active = 0 (hidden but still in database)
    """
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE menu_items SET active = ? WHERE id = ?",
        (1 if active else 0, item_id),
    )
    conn.commit()