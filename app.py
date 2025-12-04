from flask import Flask, render_template, redirect, url_for, request, session, g
from models.db import get_connection, init_db
from models import settings as settings_model
from datetime import date, timedelta  # for default date ranges

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

    @app.before_request
    def before_request():
        g.db_conn = get_connection()
        init_db(g.db_conn)

    @app.teardown_request
    def teardown_request(exception):
        conn = getattr(g, 'db_conn', None)
        if conn is not None:
            conn.close()

    @app.context_processor
    def inject_globals():
        conn = getattr(g, 'db_conn', None)
        app_settings = settings_model.get_settings(conn) if conn else {}
        default_lang = app_settings.get('language', 'en')
        lang = session.get('lang', default_lang)
        if lang not in TRANSLATIONS:
            lang = 'en'
        t = TRANSLATIONS[lang]
        return dict(settings=app_settings, t=t, current_lang=lang)

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
        ref = request.referrer or url_for('dashboard')
        return redirect(ref)

    @app.route('/')
    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard.html')

   @app.route('/income')
    def income_overview():
    """
    Show income summary for a date range.

    - If user does not give dates, we show the last 7 days by default.
    - Uses models.income.get_daily_income(...) to compute totals.
    """
    conn = getattr(g, "db_conn", None)

    # Today and 6 days ago → default last 7 days
    today = date.today()
    default_start = (today - timedelta(days=6)).isoformat()
    default_end = today.isoformat()

    # Get dates from query params (?start_date=...&end_date=...)
    start_date = request.args.get("start_date") or default_start
    end_date = request.args.get("end_date") or default_end

    daily_rows = []
    total_income = 0.0
    total_dine_in = 0.0
    total_delivery = 0.0

    if conn is not None:
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


    @app.route('/income/record', methods=['GET', 'POST'])
    
    def record_sales():
    """
    Show a form to record today's (or chosen date's) sales per menu item.

    GET:
        - Load active menu items and show a table with input boxes.
    POST:
        - Read quantities from the form for each item.
        - Call income_model.record_sales_batch(...)
    """
    conn = getattr(g, "db_conn", None)
    if conn is None:
        # Should not happen normally, but just in case
        return render_template("income/record_sales.html", menu_items=[], date_str="")

    # Default date = today
    today_str = date.today().isoformat()

    if request.method == "POST":
        # Date comes from the form (allow user to change it)
        date_str = request.form.get("date") or today_str

        # Get all menu IDs from hidden fields (one per row)
        menu_ids = request.form.getlist("menu_id")

        sales_rows = []
        for mid in menu_ids:
            # Build input names based on menu ID
            dine_in_name = f"dine_in_{mid}"
            delivery_name = f"delivery_{mid}"

            dine_in_qty_str = request.form.get(dine_in_name, "0")
            delivery_qty_str = request.form.get(delivery_name, "0")

            # Convert to int safely
            try:
                dine_in_qty = int(dine_in_qty_str) if dine_in_qty_str else 0
            except ValueError:
                dine_in_qty = 0

            try:
                delivery_qty = int(delivery_qty_str) if delivery_qty_str else 0
            except ValueError:
                delivery_qty = 0

            sales_rows.append(
                {
                    "menu_item_id": int(mid),
                    "dine_in_qty": dine_in_qty,
                    "delivery_qty": delivery_qty,
                }
            )

        # Save all rows for this date
        income_model.record_sales_batch(conn, date_str, sales_rows)

        # After saving, redirect to income overview for that date range
        return redirect(url_for("income_overview", start_date=date_str, end_date=date_str))

    # If GET: show form with all active menu items
    menu_items = menu_model.get_menu_items(conn, include_inactive=False)
    return render_template("income/record_sales.html", menu_items=menu_items, date_str=today_str)


    @app.route('/menu')
    def menu_list():
        return render_template('income/menu.html')

    @app.route('/menu/recipes')
    def menu_recipes():
        return render_template('income/recipes.html')

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

    @app.route('/wages', methods=['GET', 'POST'])
    def wages():
        if request.method == 'POST':
            pass
        return render_template('wages/index.html')

    @app.route('/settings', methods=['GET', 'POST'])
    def settings():
        conn = getattr(g, 'db_conn', None)
        app_settings = settings_model.get_settings(conn)
        if request.method == 'POST' and conn is not None:
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


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
