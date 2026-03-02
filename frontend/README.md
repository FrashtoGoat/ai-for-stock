# ai-for-stock 前端

Vue 3 + Vite + Element Plus，仅实现核心功能：健康检查、日报、新闻→交易、图表。

## 开发

```bash
# 安装依赖
npm install

# 先启动后端（在项目根目录）
# uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 启动前端（默认代理 /api、/health 到 localhost:8000）
npm run dev
```

浏览器访问 http://localhost:5173 。

## 构建

```bash
npm run build
```

产物在 `dist/`。若部署到与后端不同域名，需配置 `VITE_API_BASE` 为后端地址，例如：

```bash
VITE_API_BASE=http://your-api:8000 npm run build
```

## 页面说明

| 页面     | 功能 |
|----------|------|
| 首页     | 服务状态、快捷入口 |
| 日报     | 输入标的生成日报，可「生成并推送」到飞书/钉钉 |
| 新闻→交易 | 单/多视角建议、执行链路（仅建议或模拟下单） |
| 图表     | 输入代码与天数，展示 K 线 PNG |
