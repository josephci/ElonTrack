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
        # 💡 使用更大的視窗，確保所有元素都展開
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        print("正在前往目標網頁...")
        try:
            # 延長導航超時時間
            page.goto("https://elon-tracker.com/analytics", wait_until="load", timeout=60000)
            
            # 💡 威力優化 1：穩定處理歡迎彈窗
            print("⏳ 正在等待網頁渲染和潛在的彈窗出現...")
            
            # 在進行任何操作前，先強制等待 10 秒鐘
            # 這是為了確保 JavaScript 的歡迎彈窗完全載入並顯示出來
            page.wait_for_timeout(10000) 
            
            # 💡 威力優化 2：改用 ID 定位 Skip 按鈕 (更精準)
            # 經過對 image_1.png 中按鈕的分析，ID 通常更穩定。
            # 如果文字選取器無效，可能是網頁的 HTML 結構在無頭模式下有所不同。
            skip_button_selector = "#skip-tour-button" 
            
            # 💡 威力優化 3：使用 wait_for_selector，直到按鈕真的變亮出現
            try:
                # 最多再等 10 秒讓這個按鈕出現並準備好
                page.wait_for_selector(skip_button_selector, state="visible", timeout=10000)
                print("偵測到歡迎彈窗！正在自動點擊 'Skip' 關閉它...")
                page.locator(skip_button_selector).click()
                print("已點擊 Skip 按鈕。")
            except Exception as e:
                print(f"沒有看到 ID 為 {skip_button_selector} 的 Skip 按鈕，跳過關閉彈窗步驟。")

            # 💡 威力優化 4：多給一點時間讓背景恢復正常
            # 彈窗消失後，深色遮罩（Overlay）通常需要一小段動畫時間才會完全消失
            print("⏳ 等待背景遮罩消失並重新渲染...")
            page.wait_for_timeout(5000) 

            # 💡 威力優化 5：精準確認圖表組件載入完成
            chart_selector = "canvas"
            # 此時，canvas 必須是處於 visible 狀態（即：遮罩消失）
            page.wait_for_selector(chart_selector, state="visible", timeout=15000)
            
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
                print("⚠️ 奇怪，還是找不到 visible 的 canvas 標籤，改為全網頁截圖。")
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
            # 萬一失敗，依然拍張全景圖留底排錯
            try:
                page.screenshot(path=screenshot_path, full_page=True)
            except:
                pass
            
        finally:
            browser.close()

if __name__ == "__main__":
    run()