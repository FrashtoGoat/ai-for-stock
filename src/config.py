"""配置：从环境变量读取，不提交密钥。"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置。"""

    stock_symbols_default: str = "600519,000001"
    feishu_webhook_url: str | None = None
    dingtalk_webhook_url: str | None = None
    port: int = 8000

    # 大模型（OpenAI 兼容 API，默认 DeepSeek）
    openai_api_base: str = "https://api.deepseek.com"
    openai_api_key: str = ""
    openai_model: str = "deepseek-chat"

    # 模拟盘 / 真实交易（第三方 API；本地 SimBroker 时用 initial_cash）
    sim_broker_base_url: str = ""
    sim_broker_api_key: str = ""
    sim_broker_initial_cash: float = 1_000_000.0

    # 大盘指数代码（如沪深300）
    default_index_symbol: str = "399300"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
