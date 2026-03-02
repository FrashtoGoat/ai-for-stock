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
    llm_timeout_seconds: float = 60.0
    llm_max_retries: int = 2

    # 模拟盘 / 真实交易（第三方 API；本地 SimBroker 时用 initial_cash）
    sim_broker_base_url: str = ""
    sim_broker_api_key: str = ""
    sim_broker_initial_cash: float = 1_000_000.0
    # 实盘券商（broker_live 占位，配置后需在 broker_live 内对接具体 API）
    real_broker_base_url: str = ""
    real_broker_api_key: str = ""

    # 新闻/行情缓存 TTL（秒），0 表示不缓存
    cache_ttl_seconds: float = 60.0
    # 单次请求最大标的数量，防超时
    max_symbols_per_request: int = 20

    # 大盘指数代码（如沪深300）
    default_index_symbol: str = "399300"

    # 日报推送中的图表链接根地址（如 https://your-host:8000），为空则不附带图表链接
    public_base_url: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
