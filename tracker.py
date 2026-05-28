import os
import datetime
import requests
from playwright.sync_api import sync_playwright

SAVE_DIR = "screenshots"
os.makedirs(SAVE_DIR, exist_ok=True)

def run():
    # 讀取 GitHub Secrets 環境變數
    tg_token = os.environ.get("TELEGRAM_TOKEN")
    tg_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    now_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    screenshot_path = os.path.join(SAVE_DIR, f"elon_{now_str}.png")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        
        print("正在前往網頁...")
        page.goto("https://elon-tracker.com/analytics", wait_until="networkidle")
        
        chart_selector = "canvas"
        try:
            page.wait_for_selector(chart_selector, timeout=15000)
            chart_element = page.locator(chart_selector).first
            chart_element.screenshot(path=screenshot_path)
            print(f"✅ 截圖成功: {screenshot_path}")
            
            # 發送到 Telegram
            if tg_token and tg_chat_id:
                url = f"https://api.telegram.org/bot{tg_token}/sendPhoto"
                caption = f"📊 Elon Tracker 截圖更新\n時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
                with open(screenshot_path, 'rb') as photo:
                    files = {'photo': photo}
                    data = {'chat_id': tg_chat_id, 'caption': caption}
                    requests.post(url, files=files, data=data)
                print("飛鴿傳書！Telegram 訊息發送成功。")
                
        except Exception as e:
            print(f"❌ 發生錯誤: {e}")
            
        browser.close()

if __name__ == "__main__":
    run()