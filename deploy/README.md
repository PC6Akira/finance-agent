# 部署到 Linux 服务器（Nginx 反代 + HTTPS）

> 适用：有域名 + 云服务器（阿里云 ECS / 腾讯云 CVM 等）。
> 假设：项目位于服务器 `/opt/finance-agent`，Gradio 监听 `127.0.0.1:7860`，由 Nginx 对外。
> 本文覆盖 A 组（建表 + 监听/认证 + 反代/HTTPS）；systemd 常驻、日志轮转、SQLite WAL、akshare 缓存等属后续步骤。

## 前置
- 域名已解析到服务器公网 IP（A 记录）
- 服务器已装 Nginx、Certbot；Python 3.14（无则用 uv / pyenv 安装）

## 步骤

### 1. 拉代码 + 装依赖
```bash
git clone <你的仓库地址> /opt/finance-agent
cd /opt/finance-agent
python3.14 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 2. 配密钥与启动参数
```bash
cp .env.example .env
# 编辑 .env：填 DEEPSEEK_API_KEY / QWEN_API_KEY / BOCHA_API_KEY
# 可选：填 GRADIO_AUTH_USERNAME / GRADIO_AUTH_PASSWORD（应用层访问控制，两个都填才启用）
```
> 保持默认 `GRADIO_SERVER_NAME=127.0.0.1`（不设 0.0.0.0），让 Nginx 对外。

### 3. 申请 HTTPS 证书
```bash
sudo certbot --nginx -d your-domain.com
```
证书落在 `/etc/letsencrypt/live/your-domain.com/`，之后 `certbot renew` 自动续期。

### 4. 放 Nginx 反代配置
```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/finance-agent
# 把文件里的 your-domain.com 替换成真实域名
sudo ln -s /etc/nginx/sites-available/finance-agent /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 5. 起服务
```bash
cd /opt/finance-agent
.venv/bin/python app.py   # 启动时自动 init_db() 建表
```
浏览器访问 `https://your-domain.com`。

## 验证清单
- [ ] 首次启动无 `no such table` 报错（说明建表生效）
- [ ] 页面能加载，聊天/图表功能正常（说明 WebSocket 反代正确）
- [ ] 地址栏是 https 且无证书告警
