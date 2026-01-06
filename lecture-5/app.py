import flet as ft
import requests
from datetime import datetime

def get_area_hierarchy():
    url = "https://www.jma.go.jp/bosai/common/const/area.json" #都道府県のコードを取得
    try:
        res = requests.get(url, timeout=5).json()
        centers = res.get("centers", {})
        offices = res.get("offices", {})
        
        region_order = ["北海道", "東北", "関東甲信", "北陸", "東海", "近畿", "中国", "四国", "九州", "沖縄"]
        
        hierarchy = {} #地方選択をおこなってから都道府県選択を行うための階層データ作成
        for r_name in region_order:
            for c_code, c_info in centers.items():
                if r_name in c_info["name"]:
                    hierarchy[c_info["name"]] = {}

        for o_code, o_info in offices.items():
            parent_code = o_info.get("parent")
            if parent_code in centers:
                region_name = centers[parent_code]["name"]
                if region_name in hierarchy:
                    hierarchy[region_name][o_info["name"]] = o_code
        return hierarchy
    except Exception as e:
        print(f"Area Load Error: {e}")
        return {}

def parse_weather_icons(text): # 天気予報の文章から絵文字を取得
    icon_map = {
        "晴れ": "☀️", "はれ": "☀️", "晴": "☀️",
        "曇り": "☁️", "くもり": "☁️", "曇": "☁️",
        "雨": "🌧", "あめ": "🌧",
        "雪": "❄️", "ゆき": "❄️",
        "雷": "⚡️", "霧": "🌫", "霙": "🌨",
    }
    
    parts = []
    if "時々" in text: parts = text.split("時々")
    elif "のち" in text: parts = text.split("のち")
    elif "一時" in text: parts = [text.replace("一時", ""), ""]
    
    def get_emoji(p):
        for k, v in icon_map.items():
            if k in p: return v
        return "不明"

    if len(parts) >= 2:
        return get_emoji(parts[0]), get_emoji(parts[1])
    return get_emoji(text), ""

def get_weather_info_from_code(code):
    code = str(code)
    if code.startswith("1"): return "☀️", "", "晴れ"
    if code.startswith("2"): return "☁️", "", "くもり"
    if code.startswith("3"): return "🌧", "", "雨"
    if code.startswith("4"): return "❄️", "", "雪"
    return "", "不明"

def main(page: ft.Page): 
    page.title = "天気予報"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#F0F2F5"
    page.padding = 0

    hierarchy_data = get_area_hierarchy()
    content_area = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=20)

    def on_region_change(e): 
        region_name = region_dropdown.value
        pref_dropdown.options = [ft.dropdown.Option(name) for name in hierarchy_data[region_name].keys()]
        pref_dropdown.value = None
        pref_dropdown.disabled = False
        page.update()

    def update_weather(e):
        region_name = region_dropdown.value
        pref_name = pref_dropdown.value
        code = hierarchy_data[region_name][pref_name]
        
        try: # 天気予報データの取得
            res = requests.get(f"https://www.jma.go.jp/bosai/forecast/data/forecast/{code}.json", timeout=5).json() #都道府県の天気予報データをURLから取得
            short_f, weekly_f = res[0], res[1]
        
            d_short = short_f["timeSeries"][0]["timeDefines"]
            w_short = short_f["timeSeries"][0]["areas"][0]["weathers"]
            t_short = short_f["timeSeries"][2]["areas"][0]["temps"]
            
            d_week = weekly_f["timeSeries"][0]["timeDefines"]
            c_week = weekly_f["timeSeries"][0]["areas"][0]["weatherCodes"]
            t_min_w = weekly_f["timeSeries"][1]["areas"][0]["tempsMin"]
            t_max_w = weekly_f["timeSeries"][1]["areas"][0]["tempsMax"]

            content_area.controls.clear()
            content_area.controls.append(ft.Text(f"{pref_name} の予報", size=24, weight="bold"))
            
            cards_row = ft.Row(spacing=15, wrap=True)
            
            for i in range(5):
                if i < len(w_short):
                   
                    date_iso, w_text = d_short[i], w_short[i]
                    main_ico, sub_ico = parse_weather_icons(w_text)
                    low = t_short[i*2] if i*2 < len(t_short) else "-"
                    high = t_short[i*2+1] if i*2+1 < len(t_short) else "-"
                else:
                   
                    if i >= len(d_week): break
                    date_iso = d_week[i]
                    main_ico, sub_ico, w_text = get_weather_info_from_code(c_week[i])
                    low = t_min_w[i] if t_min_w[i] else "-"
                    high = t_max_w[i] if t_max_w[i] else "-"

                date_label = datetime.fromisoformat(date_iso).strftime("%m/%d")

                cards_row.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(date_label, weight="bold", size=16),
                            ft.Stack([
                                ft.Text(main_ico, size=45),
                                ft.Text(sub_ico, size=22, right=-5, bottom=-5, opacity=0.8) if sub_ico else ft.Container()
                            ], width=60, height=60),
                            ft.Text(w_text, size=10, height=35, text_align="center", overflow="ellipsis"),
                            ft.Row([
                                ft.Text(f"{low}℃", color="blue", weight="bold"),
                                ft.Text("/", size=10),
                                ft.Text(f"{high}℃", color="red", weight="bold"),
                            ], alignment="center")
                        ], horizontal_alignment="center", spacing=5),
                        width=140, padding=15, bgcolor="white", border_radius=12,
                        shadow=ft.BoxShadow(blur_radius=8, color="#0000001A")
                    )
                )
            content_area.controls.append(cards_row)
            page.update()
        except Exception as ex:
            content_area.controls.append(ft.Text(f"取得エラー: {ex}", color="red"))
            page.update() #ページの更新

   
    region_dropdown = ft.Dropdown(label="地方", options=[ft.dropdown.Option(n) for n in hierarchy_data.keys()], width=220, on_change=on_region_change) #地方の選択のドロップダウン
    pref_dropdown = ft.Dropdown(label="都道府県", options=[], width=220, disabled=True, on_change=update_weather)#都道府県の選択のドロップダウン

    rail = ft.NavigationRail( 
        selected_index=0, 
        label_type=ft.NavigationRailLabelType.ALL, 
        min_width=100,
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.WB_SUNNY_OUTLINED, selected_icon=ft.Icons.WB_SUNNY, label="天気"),
        ]
    )

    page.add( 
        ft.Row([
            rail,
            ft.VerticalDivider(width=1),
            ft.Container(
                content=ft.Column([
                    ft.Row([region_dropdown, pref_dropdown], spacing=20),
                    ft.Divider(height=30),
                    content_area
                ]), expand=True, padding=25
            )
        ], expand=True)
    ) 

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER) #ブラウザでアプリを起動する