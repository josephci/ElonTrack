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
        # 固定寬高為 1920x1080
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            # 加上更真實的 User Agent 和語言設定，假裝自己是真人電腦
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US"
        )
        # 在無頭模式下啟用 JavaScript (通常是預設，但確認一下)
        context.add_cookies([{'name': 'viewed_tour', 'value': 'true', 'domain': '.elon-tracker.com', 'path': '/'}])
        
        page = context.new_page()
        
        print("正在前往目標網頁 Analytics 頁面...")
        try:
            # 延長導航超時時間
            page.goto("https://elon-tracker.com/analytics", wait_until="load", timeout=90000)
            
            # 💡 終極複合大招 1：處理多步驟導覽 (Welcome -> Live Stats -> etc.)
            print("⏳ 正在等待網頁渲染和潛在的多步驟彈窗出現...")
            page.wait_for_timeout(10000) 
            
            # 定位並重複點擊 Skip 按鈕，直到找不到為止
            # 這個按鈕的文字通常是 "Skip"
            skip_button = page.locator('button:has-text("Skip")')
            attempts = 0
            while skip_button.is_visible() and attempts < 5:
                print(f"偵測到導覽彈窗 (步驟 {attempts+1})！正在自動點擊 'Skip' 關閉它...")
                skip_button.click()
                attempts += 1
                # 給彈窗切換動畫時間
                page.wait_for_timeout(2000) 

            # 💡 終極複合大招 2：DOM 暴力刪除備援 (如果 Skip 點擊無效)
            print("💥 正在執行備援 JavaScript 暴力清除剩餘黑色遮罩與彈窗...")
            page.evaluate("""
                () => {
                    // 尋找所有黑色的背景遮罩（Mask/Overlay）並直接刪除
                    const masks = document.querySelectorAll('[class*="mask"], [class*="backdrop"], [class*="overlay"], .modal-backdrop, [class*="driver"]');
                    masks.forEach(el => el.remove());
                    
                    // 尋找任何 role 為 dialog 的彈窗容器並刪除
                    const dialogs = document.querySelectorAll('div[role="dialog"], .modal');
                    dialogs.forEach(el => el.remove());
                    
                    // 恢復網頁被鎖定的滾動條
                    document.body.style.overflow = 'auto';
                    document.documentElement.style.overflow = 'auto';
                }
            """)
            
            # 刪除遮罩後等待 4 秒讓網頁重繪
            print("⏳ 彈窗與遮罩已解鎖，等待網頁重新渲染圖表...")
            page.wait_for_timeout(4000) 
            
            # 精準捕捉 `canvas` 圖表區塊
            # 我們這裡直接定位 Hourly Activity 熱力圖下方的 canvas，它比較穩定
            hourly_chart_selector = "#hourly-heatmap-container canvas"
            
            # 如果 Hourly Activity 圖表不存在，就改截 Live Stats 圖表
            if not page.locator(hourly_chart_selector).first.is_visible():
                print("找不到 Hourly Activity 圖表，改為定位 Live Stats 圖表 canvas...")
                hourly_chart_selector = "#live-stats-chart-container canvas"

            canvases = page.locator(hourly_chart_selector)
            canvas_count = canvases.count()
            print(f"在網頁上找到了 {canvas_count} 個圖表組件")
            
            if canvas_count > 0:
                # 成功找到圖表，精準截圖第一個圖表（此時彈窗已解鎖，背景變亮）
                chart_element = canvases.first
                chart_element.screenshot(path=screenshot_path)
                print(f"✅ 圖表截圖成功並儲存: {screenshot_path}")
                caption_text = f"📊 Elon Tracker 數據更新\n時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
            else:
                print("⚠️ 未能精準定位 canvas 區塊，改為全網頁備份截圖。")
                page.screenshot(path=screenshot_path, full_page=True)
                caption_text = f"📊 Elon Tracker 全景偵錯截圖\n時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"

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