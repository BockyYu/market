from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright
import pandas as pd
import time


class ItemPriceInfo(BaseModel):
    name: str = Field(title="品項")
    price: float = Field(title="價格", default=0.0)
    unit: str = Field(title="單位名稱", default="億")
    unit_value: int = Field(title="填入單位的數值", default=100000000)
    lv2_price: float = Field(title="廣價格", default=0.0)
    lv3_price: float = Field(title="故價格", default=0.0)
    lv4_price: float = Field(title="琉價格", default=0.0)
    lv1_expected_price: float = Field(title="長期望價格", default=0.0)
    lv2_expected_return: float = Field(title="廣期望收益", default=0.0)
    lv3_expected_return: float = Field(title="故期望收益", default=0.0)
    lv4_expected_return: float = Field(title="琉期望收益", default=0.0)
    lv2_net_profit: float = Field(title="廣淨利潤", default=0.0)
    lv3_net_profit: float = Field(title="故淨利潤", default=0.0)
    lv4_net_profit: float = Field(title="琉淨利潤", default=0.0)
    urls: List[str] = Field(default_factory=list, title="urls")  # 修改欄位名稱為 urls

    class Config:
        json_schema_extra = {  # 更新為新的配置名稱
            "example": {
                "name": "戒指",
                "price": 4.5,
                "unit": "億",
                "unit_value": 100000000
            }
        }

    def get_current_price(self, content: dict, index: int):
        if not content.get('bidding'):
            return
        for bid in content['bidding']:
            if bid[0] > 0:  # 如果數量大於0
                price = bid[1] / self.unit_value
                if index == 0:
                    self.price = price
                    return
                elif index == 2:
                    self.lv2_price = price
                    return
                elif index == 3:
                    self.lv3_price = price
                    return
                elif index == 4:
                    self.lv4_price = price
                    return
        return


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
                    response = page.goto(url)
                    if response:
                        content = response.json()
                        item.get_current_price(content, uidx)
                    time.sleep(0.2)  # 添加延遲避免請求過快
                item.lv1_expected_price = round(item.price / 0.8,1)  # 單價/0.8
                item.lv2_expected_return = round(item.lv2_price * 0.436, 1)  # 廣價格 * 0.436
                item.lv3_expected_return = round(item.lv3_price * 0.204, 1)  # 故價格 * 0.204
                item.lv4_expected_return = round(item.lv4_price * 0.204, 1)  # 琉價格 * 0.061
                item.lv2_net_profit = round((item.lv2_price - 3 * item.price) * 0.8515, 1)  # (廣價格-3*白板單價)*0.8515
                item.lv3_net_profit = round((item.lv3_price - 4 * item.price) * 0.8515, 1)  # (故價格-4*白板單價)*0.8515
                item.lv4_net_profit = round((item.lv4_price - 5 * item.price) * 0.8515, 1)  # (琉價格-4*白板單價)*0.8515


        except Exception as e:
            print(f"error: {e}")
            return None
        finally:
            browser.close()

    for obj in objs:
        print(obj.model_dump())


    return objs


def export_to_excel(objs: List[ItemPriceInfo], filename: str = "market_data.xlsx"):
    """
    將物品資訊匯出為Excel檔案，使用 openpyxl 引擎
    """
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
    df.to_excel(filename, index=False, engine='openpyxl')