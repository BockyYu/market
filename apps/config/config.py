import tomli
from pathlib import Path


def load_config():
    """載入配置文件"""
    # 根據新的目錄結構調整路徑
    config_path = Path(__file__).parent / "config.base.toml"

    try:
        with open(config_path, "rb") as f:
            config = tomli.load(f)
        return config
    except Exception as e:
        raise RuntimeError(f"Failed to load config: {e}")


# 載入配置
config = load_config()


# 導出配置
class UploadConfigs:
    @staticmethod
    def get(key: str):
        """
        獲取上傳相關配置

        Args:
            key: 配置鍵值

        Returns:
            配置值
        """
        config_map = {
            "Name": config["google_drive"]["name"],
            "UploadFolder": config["google_drive"]["upload_folder"],
            "Scopes": config["google_drive"]["scopes"],
        }
        return config_map.get(key)