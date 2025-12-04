from flask import Flask, render_template, redirect, url_for, request, session, g
from models.db import get_connection, init_db
from models import settings as settings_model
from datetime import date, timedelta

from models import income as income_model
from models import menu as menu_model

TRANSLATIONS = {
    'en': {
        'nav_dashboard': 'Dashboard',
        'nav_income': 'Income',
        'nav_inventory': 'Inventory',
        'nav_employees': 'Employees & Schedules',
        'nav_wages': 'Wages',
        'nav_settings': 'Settings',
        'btn_save': 'Save',
        'btn_cancel': 'Cancel',
        'title_dashboard': 'Restaurant Dashboard',
        'title_income_overview': 'Income Overview',
        'title_record_sales': 'Record Daily Sales',
        'title_menu': 'Menu Management',
        'title_inventory': 'Inventory',
        'title_inventory_suggestions': 'Inventory Suggestions',
        'title_employees': 'Employees',
        'title_schedules': 'Schedules',
        'title_replacement': 'Replacement Suggestions',
        'title_wages': 'Wage Calculation',
        'title_settings_branding': 'Branding & Contact Settings',
        'kakao_button': 'Contact via KakaoTalk',
    },
    'ko': {
        'nav_dashboard': '대시보드',
        'nav_income': '매출 관리',
        'nav_inventory': '재고 관리',
        'nav_employees': '직원 및 근무표',
        'nav_wages': '급여',
        'nav_settings': '설정',
        'btn_save': '저장',
        'btn_cancel': '취소',
        'title_dashboard': '레스토랑 대시보드',
        'title_income_overview': '매출 요약',
        'title_record_sales': '일일 매출 입력',
        'title_menu': '메뉴 관리',
        'title_inventory': '재고 현황',
        'title_inventory_suggestions': '재고 추천 / 발주 제안',
        'title_employees': '직원 관리',
        'title_schedules': '근무표',
        'title_replacement': '대체 인력 추천',
        'title_wages': '급여 계산',
        'title_settings_branding': '브랜딩 및 연락 설정',
        'kakao_button': '카카오톡으로 문의하기',
    }
}


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'change-this-secret-key'

    # ---------------------------
    # Database
    # ---------------------------
    @app.before_request
    def before_request():
        g.db_conn = get_connection()
        init_db(g.db_conn)

    @app.teardown_request
    def teardown_request(exception):
        conn = getattr(g, 'db_conn', None)
        if conn:
            conn.close()

    # ---------------------------
    # Global translations
    # ---------------------------
    @app.context_processor
    def inject_globals():
        conn = getattr(g, 'db_conn', None)
        app_settings = settings_model.get_settings(conn) if conn else {}

        default_lang = app_settings.get('language', 'en')
        lang = session.get('lang', default_lang)

        if lang not in TRANSLATIONS:
            lang = 'en'

        return dict(settings=app_settings, t=TRANSLATIONS[lang], current_lang=lang)

    # ---------------------------
    # Language route
    # ---------------------------
    @app.route('/set_language/<lang_code>')
    def set_language(lang_code):
        if lang_code not in TRANSLATIONS:
            lang_code = 'en'

        session['lang'] = lang_code

        conn = getattr(g, 'db_conn', None)
        if conn:
            current = settings_model.get_settings(conn)
            settings_model.update_settings(
                conn,
                restaurant_name=current.get('restaurant_name') or 'My Restaurant',
                language=lang_code,
                logo_path=current.get('logo_path'),
                photo_path=current.get('photo_path'),
                kakao_link=current.get('kakao_link'),
            )

        return redirect(request.referrer or url_for('dashboard'))

    # ---------------------------
    # Dashboard
    # ---------------------------
    @app.route('/')
    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard.html')

    # ---------------------------
    # Income Overview
    # ---------------------------
    @app.route('/income')
    def income_overview():
        conn = getattr(g, "db_conn", None)

        today = date.today()
        default_start = (today - timedelta(days=6)).isoformat()
        default_end = today.isoformat()

        start_date = request.args.get("start_date") or default_start
        end_date = request.args.get("end_date") or default_end

        daily_rows = []
        total_income = 0.0
        total_dine_in = 0.0
        total_delivery = 0.0

        if conn:
            daily_rows = income_model.get_daily_income(conn, start_date, end_date)
            for row in daily_rows:
                total_income += row["total_income"] or 0
                total_dine_in += row["dine_in_income"] or 0
                total_delivery += row["delivery_income"] or 0

        return render_template(
            "income/overview.html",
            start_date=start_date,
            end_date=end_date,
            daily_rows=daily_rows,
            total_income=total_income,
            total_dine_in=total_dine_in,
            total_delivery=total_delivery,
        )

    # ---------------------------
    # Record Sales
    # ---------------------------
    @app.route('/income/record', methods=['GET', 'POST'])
    def record_sales():
        conn = getattr(g, "db_conn", None)
        if not conn:
            return render_template("income/record_sales.html", menu_items=[], date_str="")

        today_str = date.today().isoformat()

        if request.method == "POST":
            date_str = request.form.get("date") or today_str
            menu_ids = request.form.getlist("menu_id")

            sales_rows = []
            for mid in menu_ids:
                dine_in_qty = int(request.form.get(f"dine_in_{mid}", "0") or 0)
                delivery_qty = int(request.form.get(f"delivery_{mid}", "0") or 0)

                sales_rows.append({
                    "menu_item_id": int(mid),
                    "dine_in_qty": dine_in_qty,
                    "delivery_qty": delivery_qty,
                })

            income_model.record_sales_batch(conn, date_str, sales_rows)
            return redirect(url_for("income_overview", start_date=date_str, end_date=date_str))

        menu_items = menu_model.get_menu_items(conn, include_inactive=False)
        return render_template("income/record_sales.html", menu_items=menu_items, date_str=today_str)

    # ---------------------------
    # Menu List
    # ---------------------------
    @app.route('/menu', methods=['GET', 'POST'])
    def menu_list():
        conn = getattr(g, "db_conn", None)
        if not conn:
            return render_template("income/menu.html", menu_items=[])

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            category = request.form.get("category", "").strip()
            price_str = request.form.get("price", "").strip()

            if name and price_str:
                try:
                    price = float(price_str)
                except ValueError:
                    price = 0.0

                if price > 0:
                    menu_model.add_menu_item(conn, name, category, price, image_path=None)

            return redirect(url_for("menu_list"))

        menu_items = menu_model.get_menu_items(conn, include_inactive=True)
        return render_template("income/menu.html", menu_items=menu_items)

    @app.route('/menu/recipes')
    def menu_recipes():
        return render_template('income/recipes.html')

    # ---------------------------
    # Inventory
    # ---------------------------
    @app.route('/inventory')
    def inventory_list():
        return render_template('inventory/list.html')

    @app.route('/inventory/update', methods=['GET', 'POST'])
    def inventory_update():
        if request.method == 'POST':
            pass
        return render_template('inventory/update.html')

    @app.route('/inventory/suggestions')
    def inventory_suggestions():
        return render_template('inventory/suggestions.html')

    # ---------------------------
    # Employees
    # ---------------------------
    @app.route('/employees')
    def employees_list():
        return render_template('employees/list.html')

    @app.route('/schedules')
    def schedules():
        return render_template('employees/schedules.html')

    @app.route('/schedules/replacement', methods=['GET', 'POST'])
    def schedules_replacement():
        if request.method == 'POST':
            pass
        return render_template('employees/replacement.html')

    # ---------------------------
    # Wages
    # ---------------------------
    @app.route('/wages', methods=['GET', 'POST'])
    def wages():
        if request.method == 'POST':
            pass
        return render_template('wages/index.html')

    # ---------------------------
    # Settings
    # ---------------------------
    @app.route('/settings', methods=['GET', 'POST'])
    def settings():
        conn = getattr(g, 'db_conn', None)
        app_settings = settings_model.get_settings(conn)

        if request.method == 'POST' and conn:
            restaurant_name = request.form.get('restaurant_name') or 'My Restaurant'
            language = request.form.get('language') or app_settings.get('language', 'en')
            kakao_link = request.form.get('kakao_link') or ''

            settings_model.update_settings(
                conn,
                restaurant_name=restaurant_name,
                language=language,
                logo_path=app_settings.get('logo_path'),
                photo_path=app_settings.get('photo_path'),
                kakao_link=kakao_link,
            )
            return redirect(url_for('settings'))

        return render_template('settings/branding.html', app_settings=app_settings)

    return app


# ---------------------------
# Run App
# ---------------------------
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
