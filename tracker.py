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
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        print("正在前往目標網頁...")
        try:
            # 延長導航超時時間
            page.goto("https://elon-tracker.com/analytics", wait_until="load", timeout=60000)
            
            # 強制等待 12 秒，讓網頁和所有的多步驟彈窗 thoroughly 載入出來
            print("⏳ 正在等待網頁和導覽彈窗 (Live Stats, etc.) 全部出現...")
            page.wait_for_timeout(12000)
            
            # 💡 終極複合大招：DOM 元素強制解鎖
            # 我們不再點擊 Skip，而是直接執行 JavaScript 把阻擋視線的「層」移除
            print("💥 正在執行 JavaScript 暴力清除黑色遮罩層，讓背景變亮...")
            page.evaluate("""
                () => {
                    // 1. 尋找所有黑色的背景遮罩（Overlay/Backdrop）並直接刪除
                    const masks = document.querySelectorAll('[class*="mask"], [class*="backdrop"], [class*="overlay"], .modal-backdrop');
                    masks.forEach(el => el.remove());
                    
                    // 2. 恢復網頁被鎖定的滾動條
                    document.body.style.overflow = 'auto';
                    document.documentElement.style.overflow = 'auto';
                    
                    // 3. 尋找多步驟導覽容器（Pop-up），並嘗試點擊其 Skip (如果有的話，做為備援)
                    const skipButton = document.querySelector('button:has-text("Skip")');
                    if(skipButton) skipButton.click();
                    
                    // 4. 強制把彈窗的層級（z-index）變得很低，不擋住圖表
                    const dialogs = document.querySelectorAll('div[role="dialog"], .popover');
                    dialogs.forEach(el => el.style.zIndex = '-9999');
                }
            """)
            
            # 刪除遮罩後等待 3 秒讓網頁重繪
            print("⏳ 黑色遮罩已強制移除，等待網頁重新渲染...")
            page.wait_for_timeout(3000)
            
            # 精準捕捉 `canvas` 圖表區塊
            chart_selector = "canvas"
            # 此時，即便有彈窗擋在 X/Y 座標上，page.locator('canvas').screenshot() 也會無視層級強制拍出 canvas 本體。
            canvases = page.locator(chart_selector)
            canvas_count = canvases.count()
            print(f"在網頁上找到了 {canvas_count} 個圖表組件")
            
            if canvas_count > 0:
                # 截取第一個圖表，Playwright 的 element screenshot 會無視上方的彈窗層級，精準拍出內容。
                # 此時背景黑色已經被我們移除，所以拍出來是白色的。
                print("💥 正在強制拍下 canvas 本體 (無視上方的彈窗層級)...")
                chart_element = canvases.first
                chart_element.screenshot(path=screenshot_path)
                print(f"✅ 圖表截圖成功並儲存: {screenshot_path}")
                caption_text = f"📊 Elon Tracker 數據更新 (彈窗遮罩已解鎖)\n時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
            else:
                # 如果還是抓不到特定區塊，就拍下全景排錯
                print("⚠️ 奇怪，還是找不到 visible 的 canvas 標籤，改為全網頁偵錯截圖。")
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