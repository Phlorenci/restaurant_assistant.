import sqlite3

DB_PATH = 'restaurant.db'


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS app_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            restaurant_name TEXT,
            logo_path TEXT,
            photo_path TEXT,
            language TEXT DEFAULT 'en',
            kakao_link TEXT
        )
        '''
    )

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            price REAL NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            image_path TEXT
        )
        '''
    )

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            menu_item_id INTEGER NOT NULL,
            ingredient_id INTEGER NOT NULL,
            quantity REAL NOT NULL,
            unit TEXT NOT NULL,
            FOREIGN KEY (menu_item_id) REFERENCES menu_items(id),
            FOREIGN KEY (ingredient_id) REFERENCES inventory_items(id)
        )
        '''
    )

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS sales_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            menu_item_id INTEGER NOT NULL,
            dine_in_qty INTEGER NOT NULL DEFAULT 0,
            delivery_qty INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (menu_item_id) REFERENCES menu_items(id)
        )
        '''
    )

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS inventory_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            unit TEXT NOT NULL,
            current_qty REAL NOT NULL DEFAULT 0,
            min_qty REAL NOT NULL DEFAULT 0
        )
        '''
    )

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS inventory_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ingredient_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            change REAL NOT NULL,
            note TEXT,
            FOREIGN KEY (ingredient_id) REFERENCES inventory_items(id)
        )
        '''
    )

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            hourly_wage REAL NOT NULL,
            active INTEGER NOT NULL DEFAULT 1
        )
        '''
    )

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            role TEXT,
            is_absent INTEGER NOT NULL DEFAULT 0,
            replacement_id INTEGER,
            hours_worked REAL,
            FOREIGN KEY (employee_id) REFERENCES employees(id),
            FOREIGN KEY (replacement_id) REFERENCES employees(id)
        )
        '''
    )

    cursor.execute('SELECT COUNT(*) AS cnt FROM app_settings')
    row = cursor.fetchone()
    if row['cnt'] == 0:
        cursor.execute(
            'INSERT INTO app_settings (id, restaurant_name, language) VALUES (1, ?, ?)',
            ('My Restaurant', 'en')
        )

    conn.commit()
