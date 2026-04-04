"""
CNKI论文下载器 - 配置管理
管理默认配置和用户自定义配置
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class DownloadSettings:
    """下载设置"""
    default_dir: Path = field(default_factory=lambda: Path.home() / "Downloads" / "CNKI")
    max_concurrent: int = 1  # 降低并发数避免CNKI限流
    timeout: int = 30000  # 30秒
    retry_times: int = 2
    chunk_size: int = 1024


@dataclass
class BrowserSettings:
    """浏览器设置"""
    headless: bool = False  # 是否无头模式
    slow_mo: int = 500      # 操作延迟（毫秒）- 增加延迟以模拟真实用户
    user_agent: Optional[str] = None
    viewport_width: int = 1366  # 改为更常见的分辨率
    viewport_height: int = 768
    # 反检测参数
    locale: str = "zh-CN"
    timezone: str = "Asia/Shanghai"
    # 额外的浏览器选项
    args: list = field(default_factory=lambda: [
        "--disable-blink-features=AutomationControlled",  # 隐藏自动化特征
        "--disable-dev-shm-usage",  # 避免内存问题
        "--no-sandbox",  # 禁用沙箱（某些环境需要）
        "--disable-setuid-sandbox",
        "--disable-web-security",  # 允许跨域
    ])


@dataclass
class FileSettings:
    """文件设置"""
    sanitize_filename: bool = True
    max_filename_length: int = 200
    conflict_strategy: str = "append_number"  # append_number, skip, overwrite
    encoding: str = "utf-8"


@dataclass
class DefaultValues:
    """默认值"""
    doc_type: str = "学术期刊"
    count: int = 10
    language: str = "CHS"
    uniplatform: str = "NZKPT"


@dataclass
class LoggingSettings:
    """日志设置"""
    enabled: bool = True
    level: str = "INFO"
    log_dir: Path = field(default_factory=lambda: Path.home() / "cnki_downloader_logs")
    max_log_size: int = 10485760  # 10MB


@dataclass
class Config:
    """总配置"""
    download: DownloadSettings = field(default_factory=DownloadSettings)
    browser: BrowserSettings = field(default_factory=BrowserSettings)
    file: FileSettings = field(default_factory=FileSettings)
    defaults: DefaultValues = field(default_factory=DefaultValues)
    logging: LoggingSettings = field(default_factory=LoggingSettings)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "download_settings": asdict(self.download),
            "browser_settings": asdict(self.browser),
            "file_settings": asdict(self.file),
            "default_values": asdict(self.defaults),
            "logging": asdict(self.logging)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """从字典创建配置"""
        config = cls()

        if "download_settings" in data:
            config.download = DownloadSettings(**{
                k: Path(v) if k == "default_dir" else v
                for k, v in data["download_settings"].items()
            })

        if "browser_settings" in data:
            config.browser = BrowserSettings(**data["browser_settings"])

        if "file_settings" in data:
            config.file = FileSettings(**data["file_settings"])

        if "default_values" in data:
            config.defaults = DefaultValues(**data["default_values"])

        if "logging" in data:
            log_data = data["logging"]
            if "log_dir" in log_data:
                log_data["log_dir"] = Path(log_data["log_dir"])
            config.logging = LoggingSettings(**log_data)

        return config


class ConfigManager:
    """配置管理器"""

    DEFAULT_CONFIG_PATH = Path.home() / ".cnki_downloader" / "config.json"

    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径（默认使用 ~/.cnki_downloader/config.json）
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config = Config()

        # 如果配置文件存在，加载用户配置
        if self.config_path.exists():
            self.load()

    def load(self) -> Config:
        """
        加载配置文件

        Returns:
            Config: 配置对象
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.config = Config.from_dict(data)
        except Exception as e:
            print(f"⚠️ 加载配置文件失败: {e}")
            print("使用默认配置")

        return self.config

    def save(self) -> None:
        """保存配置到文件"""
        try:
            # 确保配置目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # 保存配置
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config.to_dict(), f, indent=2, ensure_ascii=False)

            print(f"✅ 配置已保存到: {self.config_path}")
        except Exception as e:
            print(f"❌ 保存配置文件失败: {e}")

    def get(self) -> Config:
        """获取当前配置"""
        return self.config

    def update(self, **kwargs) -> None:
        """
        更新配置

        Args:
            **kwargs: 要更新的配置项
                示例: update(max_concurrent=5, headless=True)
        """
        for key, value in kwargs.items():
            if hasattr(self.config.download, key):
                setattr(self.config.download, key, value)
            elif hasattr(self.config.browser, key):
                setattr(self.config.browser, key, value)
            elif hasattr(self.config.file, key):
                setattr(self.config.file, key, value)
            elif hasattr(self.config.defaults, key):
                setattr(self.config.defaults, key, value)
            elif hasattr(self.config.logging, key):
                setattr(self.config.logging, key, value)

    def reset(self) -> None:
        """重置为默认配置"""
        self.config = Config()


# 测试代码
if __name__ == "__main__":
    # 创建配置管理器
    manager = ConfigManager()

    # 获取配置
    config = manager.get()
    print("当前配置:")
    print(json.dumps(config.to_dict(), indent=2, ensure_ascii=False, default=str))

    # 更新配置
    print("\n更新配置...")
    manager.update(max_concurrent=5, headless=True)
    manager.save()

    # 重新加载
    manager2 = ConfigManager()
    config2 = manager2.get()
    print(f"\n并发数: {config2.download.max_concurrent}")
    print(f"无头模式: {config2.browser.headless}")
