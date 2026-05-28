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
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        print("正在前往目標網頁...")
        try:
            page.goto("https://elon-tracker.com/analytics", wait_until="networkidle", timeout=60000)
            
            # 先等待 5 秒讓網頁和彈窗全部加載出來
            print("⏳ 等待網頁加載...")
            page.wait_for_timeout(5000)
            
            # 💡 終極大招：直接用 JavaScript 刪除所有彈窗與遮罩層
            print("💥 正在執行 JavaScript 暴力清除彈窗與遮罩...")
            page.evaluate("""
                () => {
                    // 1. 尋找並刪除所有可能包含 'Welcome to' 或 'Skip' 的彈窗容器
                    const dialogs = document.querySelectorAll('div[role="dialog"], .modal, [class*="modal"], [class*="popup"]');
                    dialogs.forEach(el => el.remove());
                    
                    # 2. 尋找所有黑色的背景遮罩（Overlay）並刪除
                    # 依據你的截圖，遮罩通常是透明度黑底，或者帶有 backdrop-blur 的層
                    const backdrops = document.querySelectorAll('[class*="backdrop"], [class*="overlay"], [class*="mask"]');
                    backdrops.forEach(el => el.remove());
                    
                    // 3. 恢復網頁被鎖定的滾動條與背景亮度
                    document.body.style.overflow = 'auto';
                    document.body.style.pointerEvents = 'auto';
                    document.documentElement.style.overflow = 'auto';
                    
                    // 嘗試直接清除第三方 Tour 插件產生的外殼
                    const driverPopups = document.querySelectorAll('.driver-popover-item, .driver-overlay');
                    driverPopups.forEach(el => el.remove());
                }
            """)
            
            # 刪除後等待 2 秒讓網頁重繪
            print("⏳ 彈窗已強制移除，等待網頁重新渲染...")
            page.wait_for_timeout(2000)
            
            # 檢查圖表是否存在
            chart_selector = "canvas"
            canvases = page.locator(chart_selector)
            canvas_count = canvases.count()
            print(f"在網頁上找到了 {canvas_count} 個圖表組件")
            
            if canvas_count > 0:
                # 截取第一個圖表區塊
                chart_element = canvases.first
                chart_element.screenshot(path=screenshot_path)
                print(f"✅ 圖表截圖成功: {screenshot_path}")
                caption_text = f"📊 Elon Tracker 數據更新\n時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
            else:
                # 如果還是抓不到特定區塊，就拍下被我們「強制去彈窗」後的網頁全景
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