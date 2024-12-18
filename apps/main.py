import os
import json
from apps.service.google_upload.upload import do_upload
from apps.service.market import get_market_data, export_to_excel

script_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(script_dir, 'data.json')
with open(json_path, 'r', encoding='utf-8') as f:
    config = json.load(f)


if __name__ == "__main__":
    try:
        market_data = get_market_data(config)
        export_to_excel(market_data)
        do_upload()
    except Exception as e:
        print(f"Program failed: {e}")