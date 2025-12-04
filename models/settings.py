from sqlite3 import Connection


def get_settings(conn: Connection) -> dict:
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM app_settings WHERE id = 1')
    row = cursor.fetchone()
    if row is None:
        return {
            'restaurant_name': 'My Restaurant',
            'logo_path': None,
            'photo_path': None,
            'language': 'en',
            'kakao_link': '',
        }
    return {
        'restaurant_name': row['restaurant_name'] or 'My Restaurant',
        'logo_path': row['logo_path'],
        'photo_path': row['photo_path'],
        'language': row['language'] or 'en',
        'kakao_link': row['kakao_link'] or '',
    }


def update_settings(conn: Connection, restaurant_name: str, language: str = 'en',
                    logo_path: str | None = None, photo_path: str | None = None,
                    kakao_link: str | None = None) -> None:
    cursor = conn.cursor()
    cursor.execute(
        '''
        UPDATE app_settings
        SET restaurant_name = ?,
            logo_path = ?,
            photo_path = ?,
            language = ?,
            kakao_link = ?
        WHERE id = 1
        ''',
        (restaurant_name, logo_path, photo_path, language, kakao_link),
    )
    conn.commit()
