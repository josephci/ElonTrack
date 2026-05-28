import os
import datetime
import requests
from playwright.sync_api import sync_playwright

SAVE_DIR = "screenshots"
os.makedirs(SAVE_DIR, exist_ok=True)

def run():
    tg_token = os.environ.get("TELEGRAM_TOKEN")
    tg_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    now_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    screenshot_path = os.path.join(SAVE_DIR, f"elon_{now_str}.png")
    
    with sync_playwright() as p:
        # 模擬一般的 Chrome 瀏覽器，減少被網站擋下來的機率
        browser = p.chromium.launch(headless=True)
        
        # 💡 關鍵優化：加上 user_agent，假裝自己是真正的 Windows 電腦瀏覽器
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        print("正在前往目標網頁...")
        try:
            # 延長超時時間到 30 秒，確保網路慢時也能載入
            page.goto("https://elon-tracker.com/analytics", wait_until="networkidle", timeout=30000)
            
            # 給網頁多額外 3 秒鐘的時間穩定渲染圖表
            page.wait_for_timeout(3000)
            
            # 檢查目標網頁上所有的 canvas 標籤
            canvases = page.locator("canvas")
            canvas_count = canvases.count()
            print(f"在網頁上找到了 {canvas_count} 個圖表(canvas)組件")
            
            if canvas_count > 0:
                # 成功找到圖表，精準截圖第一個圖表
                chart_element = canvases.first
                chart_element.screenshot(path=screenshot_path)
                print(f"✅ 圖表截圖成功並儲存: {screenshot_path}")
                caption_text = f"📊 Elon Tracker 數據更新\n時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
            else:
                # 🔍 偵錯模式：找不到圖表時，截取「整個網頁」看看是不是變白畫面或被擋了
                print("⚠️ 找不到 canvas 標籤，啟動備用方案：截取全網頁畫面進行排錯。")
                page.screenshot(path=screenshot_path, full_page=True)
                caption_text = f"⚠️ 警告：找不到圖表組件，此為網頁全景排錯截圖。\n時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"

            # 發送到 Telegram
            if tg_token and tg_chat_id and os.path.exists(screenshot_path):
                url = f"https://api.telegram.org/bot{tg_token}/sendPhoto"
                with open(screenshot_path, 'rb') as photo:
                    files = {'photo': photo}
                    data = {'chat_id': tg_chat_id, 'caption': caption_text}
                    requests.post(url, files=files, data=data)
                print("🚀 Telegram 訊息發送完畢。")
                
        except Exception as e:
            print(f"❌ 腳本執行期間發生嚴重錯誤: {e}")
            
        finally:
            browser.close()

if __name__ == "__main__":
    run()