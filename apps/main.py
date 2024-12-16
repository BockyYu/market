import os
import sys
from playwright.sync_api import sync_playwright
import json
import time

# 方法1：使用絕對路徑
script_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(script_dir, 'ring.json')
with open(json_path, 'r', encoding='utf-8') as f:
    config = json.load(f)


def generate_urls(config):
    all_urls = []
    for item in config['data']:
        urls = []
        for lv in range(item['max_lv']):
            url = item['url'].format(
                main_key=item['main_key'],
                lv=lv
            )
            urls.append(url)
        all_urls.extend(urls)
    return all_urls


def get_market_data():
    urls = generate_urls(config)
    all_data = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            for idx, url in enumerate(urls):
                response = page.goto(url)
                if response:
                    content = response.json()
                    all_data[f'sub_key_{idx}'] = content

                    # print(f"\n----- sub_key_{idx} 的數據 -----")
                    # print(json.dumps(content, indent=2, ensure_ascii=False))

                    # 儲存到獨立文件
                    # with open(f'market_data_sub_key_{idx}.json', 'w', encoding='utf-8') as f:
                    #     json.dump(content, indent=2, ensure_ascii=False, fp=f)
                time.sleep(0.2)  # 添加延遲避免請求過快

            # 儲存所有數據到一個文件
            with open('all_market_data.json', 'w', encoding='utf-8') as f:
                json.dump(all_data, indent=2, ensure_ascii=False, fp=f)

            return all_data

        except Exception as e:
            print(f"錯誤: {e}")
            return None

        finally:
            browser.close()


def get_resource_path(relative_path):
    """獲取資源文件的路徑，支援開發環境和打包後的環境"""
    if getattr(sys, 'frozen', False):
        # 如果是打包後的執行文件
        base_path = sys._MEIPASS
    else:
        # 如果是開發環境
        base_path = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.join(base_path, '..')

    return os.path.join(base_path, relative_path)


def ensure_playwright_browser():
    try:
        import subprocess
        subprocess.run(['playwright', 'install', 'chromium'], check=True)
    except Exception as e:
        print(f"Error installing browser: {e}")
        sys.exit(1)


if __name__ == "__main__":
    ensure_playwright_browser()
    result = get_market_data()