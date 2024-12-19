from datetime import datetime
from apps.model import ItemPriceInfo
from typing import List
from playwright.sync_api import sync_playwright
import pandas as pd
import time


def get_market_data(config: dict):
    objs = []
    for item in config['data']:
        urls = []
        for lv in range(item['max_lv']):
            url = item['url'].format(main_key=item['main_key'], lv=lv)
            urls.append(url)
        obj = ItemPriceInfo(
            name=item['chinese_name'],
            urls=urls
        )
        objs.append(obj)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            for idx, item in enumerate(objs):
                for uidx, url in enumerate(item.urls):
                    try:
                        response = page.goto(url)
                        if response and response.status == 200:  # 確保請求成功
                            content = response.json()
                            item.get_current_price(content, uidx)
                        time.sleep(0.2)
                    except Exception as e:
                        print(f"Error processing URL {url}: {e}")
                        continue

                try:
                    item.lv1_expected_price = round(item.price / 0.8, 1)
                    item.lv2_expected_return = round(item.lv2_price * 0.436, 1)
                    item.lv3_expected_return = round(item.lv3_price * 0.204, 1)
                    item.lv4_expected_return = round(item.lv4_price * 0.204, 1)
                    item.lv2_net_profit = round((item.lv2_price - 3 * item.price) * 0.8515, 1)
                    item.lv3_net_profit = round((item.lv3_price - 4 * item.price) * 0.8515, 1)
                    item.lv4_net_profit = round((item.lv4_price - 5 * item.price) * 0.8515, 1)
                except Exception as e:
                    print(f"Error calculating values for item {item.name}: {e}")
                    continue

        except Exception as e:
            print(f"Critical error: {e}")
        finally:
            browser.close()

    if not objs:
        raise ValueError("No data was collected")

    return objs


def export_to_excel(objs: List[ItemPriceInfo], filename: str = "market_data_{date}.xlsx"):
    """
    將物品資訊匯出為Excel檔案，使用 openpyxl 引擎
    """
    if not objs:
        raise ValueError("No data to export")

    data = {
        '品項': [],
        '單價': [],
        '廣價格': [],
        '故價格': [],
        '琉價格': [],
        '長期望價格': [],
        '廣期望收益': [],
        '故期望收益': [],
        '琉期望收益': [],
        '廣淨利潤': [],
        '故淨利潤': [],
        '琉淨利潤': []
    }

    for obj in objs:
        data['品項'].append(obj.name)
        data['單價'].append(obj.price)
        data['廣價格'].append(obj.lv2_price)
        data['故價格'].append(obj.lv3_price)
        data['琉價格'].append(obj.lv4_price)
        data['長期望價格'].append(obj.lv1_expected_price)
        data['廣期望收益'].append(obj.lv2_expected_return)
        data['故期望收益'].append(obj.lv3_expected_return)
        data['琉期望收益'].append(obj.lv4_expected_return)
        data['廣淨利潤'].append(obj.lv2_net_profit)
        data['故淨利潤'].append(obj.lv3_net_profit)
        data['琉淨利潤'].append(obj.lv4_net_profit)

    df = pd.DataFrame(data)

    current_time = datetime.now()
    filename = filename.format(date=current_time.strftime('%Y%m%d'))

    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='市場資料')

        worksheet = writer.sheets['市場資料']
        last_row = len(df) + 2
        update_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
        worksheet.cell(row=last_row, column=1, value=f'最後更新時間：{update_time}')