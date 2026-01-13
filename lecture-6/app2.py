import flet as ft
import requests
import sqlite3 # SQLiteの追加
from datetime import datetime

def init_db():
    conn = sqlite3.connect('weather.db')
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS forecasts (
            forecast_date TEXT,
            area_code TEXT,
            area_name TEXT,
            weather_text TEXT,
            temp_low TEXT,
            temp_high TEXT,
            saved_at TEXT,
            PRIMARY KEY (forecast_date, area_code, saved_at)
        )
    ''')
    conn.commit()
    conn.close()


def save_to_db(date_iso, area_code, area_name, weather, low, high):
    forecast_date = date_iso[:10]
    saved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect('weather.db')
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO forecasts
        (forecast_date, area_code, area_name, weather_text, temp_low, temp_high, saved_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (forecast_date, area_code, area_name, weather, str(low), str(high), saved_at))
    conn.commit()
    conn.close()


def get_from_db(forecast_date, area_code):
    conn = sqlite3.connect('weather.db')
    cur = conn.cursor()
    cur.execute('''
        SELECT *
        FROM forecasts
        WHERE forecast_date = ? AND area_code = ?
        ORDER BY saved_at DESC
        LIMIT 1
    ''', (forecast_date, area_code))
    row = cur.fetchone()
    conn.close()
    return row


def get_area_hierarchy():
    url = "https://www.jma.go.jp/bosai/common/const/area.json"
    try:
        res = requests.get(url, timeout=5).json()
        centers = res.get("centers", {})
        offices = res.get("offices", {})
        region_order = ["北海道", "東北", "関東甲信", "北陸", "東海", "近畿", "中国", "四国", "九州", "沖縄"]
        hierarchy = {}
        for r_name in region_order:
            for c_code, c_info in centers.items():
                if r_name in c_info["name"]: hierarchy[c_info["name"]] = {}
        for o_code, o_info in offices.items():
            parent_code = o_info.get("parent")
            if parent_code in centers:
                region_name = centers[parent_code]["name"]
                if region_name in hierarchy: hierarchy[region_name][o_info["name"]] = o_code
        return hierarchy
    except: return {}

def parse_weather_icons(text):
    icon_map = {"晴れ": "☀️", "曇り": "☁️", "雨": "🌧", "雪": "❄️", "雷": "⚡️"}
    for k, v in icon_map.items():
        if k in text: return v, ""
    return "不明", ""

def get_weather_info_from_code(code):
    mapping = {"1": ("☀️", "晴れ"), "2": ("☁️", "くもり"), "3": ("🌧", "雨"), "4": ("❄️", "雪")}
    return mapping.get(str(code)[0], ("❓", "不明"))

def main(page: ft.Page):
    init_db() # 起動時にDB作成
    page.title = "天気予報"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#F0F2F5"
    
    hierarchy_data = get_area_hierarchy()
    content_area = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=20)

    # カード作成用の関数
    def create_weather_card(date_label, main_ico, sub_ico, w_text, low, high):
        return ft.Container(
            content=ft.Column([
                ft.Text(date_label, weight="bold", size=16),
                ft.Text(main_ico, size=45),
                ft.Text(w_text, size=10, height=35, text_align="center"),
                ft.Row([
                    ft.Text(f"{low}℃", color="blue", weight="bold"),
                    ft.Text("/", size=10),
                    ft.Text(f"{high}℃", color="red", weight="bold"),
                ], alignment="center")
            ], horizontal_alignment="center", spacing=5),
            width=140, padding=15, bgcolor="white", border_radius=12,
            shadow=ft.BoxShadow(blur_radius=8, color="#0000001A")
        )

    # DB検索用の関数
    def search_db(e):
        if not date_picker.value or not pref_dropdown.value: return
        
        target_date = date_picker.value.strftime("%Y-%m-%d")
        region_name = region_dropdown.value
        code = hierarchy_data[region_name][pref_dropdown.value]
        
        row = get_from_db(target_date, code)
        
        content_area.controls.clear()
        if row:
            # DBにデータがあった場合
            ico, _ = parse_weather_icons(row[3])
            content_area.controls.append(ft.Text(f"DBから取得: {row[2]} ({row[0]})", size=20, color="green"))
            content_area.controls.append(create_weather_card(row[0], ico, "", row[3], row[4], row[5]))
        else:
            # DBにデータがない場合
            content_area.controls.append(
                ft.Text(f"⚠️ {target_date} のデータはDBにありません。\n一度予報を取得してから再度お試しください。", color="red", text_align="center")
            )
        page.update()

    def on_region_change(e):
        region_name = region_dropdown.value
        pref_dropdown.options = [ft.dropdown.Option(name) for name in hierarchy_data[region_name].keys()]
        pref_dropdown.disabled = False
        page.update()

    def update_weather(e):
        region_name = region_dropdown.value
        pref_name = pref_dropdown.value
        code = hierarchy_data[region_name][pref_name]
        
        try:
            res = requests.get(f"https://www.jma.go.jp/bosai/forecast/data/forecast/{code}.json").json()
            short_f = res[0]
            
            d_list = short_f["timeSeries"][0]["timeDefines"]
            w_list = short_f["timeSeries"][0]["areas"][0]["weathers"]
            t_list = short_f["timeSeries"][2]["areas"][0]["temps"]

            content_area.controls.clear()
            content_area.controls.append(ft.Text(f"{pref_name} の最新予報 (DBへ保存完了)", size=22, weight="bold"))
            cards_row = ft.Row(spacing=15, wrap=True)
            
            for i in range(len(w_list)):
                date_iso = d_list[i]
                w_text = w_list[i]
                low = t_list[i*2] if i*2 < len(t_list) else "-"
                high = t_list[i*2+1] if i*2+1 < len(t_list) else "-"
                
                # ここでDBに保存
                save_to_db(date_iso, code, pref_name, w_text, low, high)
                
                main_ico, sub_ico = parse_weather_icons(w_text)
                date_label = datetime.fromisoformat(date_iso).strftime("%m/%d")
                cards_row.controls.append(create_weather_card(date_label, main_ico, sub_ico, w_text, low, high))
            
            content_area.controls.append(cards_row)
            page.update()
        except Exception as ex:
            content_area.controls.append(ft.Text(f"エラー: {ex}", color="red"))
            page.update()

    # カレンダー設定
    date_picker = ft.DatePicker(on_change=search_db)
    page.overlay.append(date_picker)

    region_dropdown = ft.Dropdown(label="地方", options=[ft.dropdown.Option(n) for n in hierarchy_data.keys()], width=200, on_change=on_region_change)
    pref_dropdown = ft.Dropdown(label="都道府県", options=[], width=200, disabled=True, on_change=update_weather)
    db_search_btn = ft.ElevatedButton(
    "日付から検索", 
    icon=ft.Icons.CALENDAR_MONTH, 
    on_click=lambda _: setattr(date_picker, "open", True) or page.update()
)

    page.add(
        ft.Container(
            content=ft.Column([
                ft.Row([region_dropdown, pref_dropdown, db_search_btn], alignment="center", spacing=20),
                ft.Divider(),
                content_area
            ]), padding=20, expand=True
        )
    )

if __name__ == "__main__":
    ft.app(target=main)