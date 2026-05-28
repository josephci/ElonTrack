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
        # 固定寬高為 1920x1080，這樣點擊的座標才會精準
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        print("正在前往目標網頁...")
        try:
            page.goto("https://elon-tracker.com/analytics", wait_until="networkidle", timeout=60000)
            
            # 強制等待 8 秒，讓網頁和彈窗徹底定位
            print("⏳ 等待網頁完全載入...")
            page.wait_for_timeout(8000)
            
            # 💡 核心大招：座標盲點法
            # 在 1920x1080 的解析度下，那個 Welcome 彈窗的 "Skip" 按鈕大約在螢幕正中央偏下的位置
            # 我們直接對著 X: 1070, Y: 600 的位置點擊滑鼠左鍵
            print("🎯 正在往座標 (X: 1070, Y: 600) 模擬真人滑鼠點擊 'Skip'...")
            page.mouse.click(1070, 600)
            
            # 萬一沒點準，我們對著右上角的 "X" 關閉按鈕 (大約在 X: 1110, Y: 300) 再點一下
            page.wait_for_timeout(1000)
            print("🎯 嘗試點擊右上角關閉按鈕備用座標 (X: 1110, Y: 300)...")
            page.mouse.click(1110, 300)
            
            # 點完後等待 4 秒，讓遮罩黑影完全淡出
            print("⏳ 等待遮罩動畫消失...")
            page.wait_for_timeout(4000)
            
            # 檢查圖表
            chart_selector = "canvas"
            canvases = page.locator(chart_selector)
            canvas_count = canvases.count()
            print(f"在網頁上找到了 {canvas_count} 個圖表組件")
            
            if canvas_count > 0:
                # 成功找到圖表，精準截圖第一個圖表
                chart_element = canvases.first
                chart_element.screenshot(path=screenshot_path)
                print(f"✅ 圖表截圖成功: {screenshot_path}")
                caption_text = f"📊 Elon Tracker 數據更新\n時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
            else:
                # 如果還是抓不到特定區塊，就拍下全景
                print("⚠️ 未能精準定位 canvas 區塊，改為全網頁截圖。")
                page.screenshot(path=screenshot_path, full_page=True)
                caption_text = f"📊 Elon Tracker 全景數據備份\n時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"

            # 發送到 Telegram
            if tg_token and tg_chat_id and os.path.exists(screenshot_path):
                url = f"https://api.telegram.org/bot{tg_token}/sendPhoto"
                with open(screenshot_path, 'rb') as photo:
                    files = {'photo': photo}
                    data = {'chat_id': tg_chat_id, 'caption': caption_text}
                    requests.post(url, files=files, data=data)
                print("🚀 Telegram 訊息發送完畢。")
                
        except Exception as e:
            print(f"❌ 發生嚴重錯誤: {e}")
            try:
                page.screenshot(path=screenshot_path, full_page=True)
            except:
                pass
            
        finally:
            browser.close()

if __name__ == "__main__":
    run()