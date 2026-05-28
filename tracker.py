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
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        print("正在前往目標網頁...")
        try:
            page.goto("https://elon-tracker.com/analytics", wait_until="networkidle", timeout=30000)
            
            # 💡 關鍵步驟 1：處理「Welcome to ElonTracker」彈窗
            # 根據你提供的截圖，我們定位那個「Skip」按鈕
            skip_button_selector = "button:has-text('Skip')"
            
            # 檢查網頁上是否有這個 Skip 按鈕
            if page.locator(skip_button_selector).is_visible():
                print("偵測到歡迎彈窗！正在自動點擊 'Skip' 關閉它...")
                page.locator(skip_button_selector).click()
                # 點擊後稍微等 1 秒讓彈窗動畫消失
                page.wait_for_timeout(1000)
            else:
                print("沒有看到歡迎彈窗，直接進行下一步。")
            
            # 💡 關鍵步驟 2：再次確認圖表組件是否載入完畢
            chart_selector = "canvas"
            page.wait_for_selector(chart_selector, timeout=15000)
            
            canvases = page.locator(chart_selector)
            canvas_count = canvases.count()
            print(f"在網頁上找到了 {canvas_count} 個圖表組件")
            
            if canvas_count > 0:
                # 成功找到圖表，精準截圖第一個圖表（此時彈窗已關閉，背景變亮）
                chart_element = canvases.first
                chart_element.screenshot(path=screenshot_path)
                print(f"✅ 圖表截圖成功並儲存: {screenshot_path}")
                caption_text = f"📊 Elon Tracker 數據更新\n時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
            else:
                print("⚠️ 奇怪，還是找不到 canvas 標籤，改為全網頁截圖。")
                page.screenshot(path=screenshot_path, full_page=True)
                caption_text = f"⚠️ 警告：找不到圖表組件，此為網頁全景截圖。\n時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"

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
            # 萬一失敗，依然拍張全景圖留底排錯
            try:
                page.screenshot(path=screenshot_path, full_page=True)
            except:
                pass
            
        finally:
            browser.close()

if __name__ == "__main__":
    run()