from pydantic import BaseModel, Field
from typing import List


class ItemPriceInfo(BaseModel):
    name: str = Field(title="品項")
    price: float = Field(title="價格", default=0.0)
    unit: str = Field(title="單位名稱", default="億")
    unit_value: int = Field(title="填入單位的數值", default=100000000)
    lv1_price: float = Field(title="長價格", default=0.0)
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
        price_attrs = {0: 'price', 1: 'lv1_price', 2: 'lv2_price', 3: 'lv3_price', 4: 'lv4_price'}
        if not content.get('bidding'):
            return

        bidding = content['bidding']
        if len(bidding) == 1:
            d = bidding[0]
            count, amount = d[0], d[1]
            price = amount / self.unit_value
            setattr(self, price_attrs[index], price)
            return
        for bid in reversed(bidding):  # 從最後的元素開始取得資料
            count, amount = bid[0], bid[1]
            if count > 0:  # 如果數量大於0
                price = amount / self.unit_value
                setattr(self, price_attrs[index], price)
                return
        return
