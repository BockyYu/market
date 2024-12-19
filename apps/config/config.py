import tomli
from pathlib import Path


def deep_merge_dict(base: dict, override: dict) -> None:
    """合併字典，override 會覆蓋 base 中的對應值"""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge_dict(base[key], value)
        else:
            base[key] = value


def load_config():
    """載入配置文件"""
    config_dir = Path(__file__).parent
    base_config_path = config_dir / "config.base.toml"
    local_config_path = config_dir / "config.local.toml"

    try:
        # 載入基礎配置
        with open(base_config_path, "rb") as f:
            config = tomli.load(f)

        # 如果存在本地配置，則合併覆蓋
        if local_config_path.exists():
            with open(local_config_path, "rb") as f:
                local_config = tomli.load(f)
                deep_merge_dict(config, local_config)

        return config
    except Exception as e:
        raise RuntimeError(f"Failed to load config: {e}")


config = load_config()


class Configs:
    @staticmethod
    def get(key: str):
        """
        獲取上傳相關配置

        Args:
            key: 配置鍵值

        Returns:
            配置值
        """
        upload = {
            "Name": config["upload"]["name"],
            "UploadFolder": config["upload"]["upload_folder"],
            "Scopes": config["upload"]["scopes"],
        }
        conf = {"Upload": upload}
        return conf.get(key)