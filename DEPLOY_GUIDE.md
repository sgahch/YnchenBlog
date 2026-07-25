# Ynchen. ~ 博客系统 — 生产环境部署方案

---

## 一、项目技术栈分析

### 1.1 架构总览

```
用户浏览器 (HTTPS)
      │
      ▼
┌─ Nginx (宝塔面板) ─────────────────────────────────────┐
│                                                          │
│  /api/*      → http://127.0.0.1:6789/api/*   (FastAPI) │
│  /uploads/*  → http://127.0.0.1:6789/uploads/* (FastAPI)│
│  /admin/*    → FastAPI 内置静态文件服务                    │
│  /*          → http://127.0.0.1:3000           (Next.js)│
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 1.2 各组件详情

| 组件 | 技术栈 | 端口 | 部署方式 |
|------|--------|------|----------|
| **前端博客** | Next.js 16 + React 19 + TypeScript + Tailwind CSS 4 | 3000 | `next start` (SSR 模式，非静态导出) |
| **管理后台** | Vue 3 + Vite 8 + Element Plus + Pinia (vue-pure-admin) | — | 纯静态 SPA，构建后由 FastAPI 托管 |
| **后端 API** | FastAPI (Python 3.10+) + SQLModel + Uvicorn | 6789 | `uvicorn` 进程 |
| **数据库** | MySQL 8.0+ | 3306 | 导入 `init_db.sql` |
| **对象存储** | MinIO | 9000/9001 | 自托管，Docker Compose 一键启动 |

### 1.3 关键文件清单

| 文件 | 作用 |
|------|------|
| `Kirameku/` | Next.js 前端博客项目 |
| `Kirameku/package.json` | 前端依赖 & 脚本 (`pnpm build` / `next start`) |
| `Kirameku/next.config.ts` | Next.js 配置 (rewrites 代理规则、图片域名白名单) |
| `Kirameku/siteConfig.ts` | 博客站点配置 (标题、社交链接、歌单等) |
| `Kirameku/.env.example` | 前端环境变量模板 |
| `Kirameku-backend/` | FastAPI 后端项目 |
| `Kirameku-backend/requirements.txt` | Python 依赖 |
| `Kirameku-backend/start.py` | 本地开发启动脚本 |
| `Kirameku-backend/app/main.py` | FastAPI 应用入口 |
| `Kirameku-backend/app/config.py` | 后端配置 (读取 .env) |
| `Kirameku-backend/app/database.py` | 数据库连接 & 自动建表 |
| `Kirameku-backend/.env` | 后端环境变量 (实际使用的) |
| `Kirameku-backend/.env.example` | 后端环境变量模板 |
| `Kirameku-backend/init_db.sql` | 数据库建表 + 初始数据脚本 |
| `Kirameku-backend/admin/` | Vue 管理后台前端项目 |
| `Kirameku-backend/admin/package.json` | 管理后台依赖 & 构建脚本 |
| `Kirameku-backend/admin/Dockerfile` | 管理后台 Docker 构建 (备用) |

---

## 二、部署前准备

### 2.1 依赖服务确认

| 依赖 | 是否必需 | 说明 |
|------|----------|------|
| MySQL 8.0+ | ✅ **必需** | 主数据库，18 张业务表 |
| MinIO | ✅ **必需** | 自托管对象存储，图片/文件上传 |
| GitHub OAuth | ⚠️ 可选 | 访客评论/留言登录，不配则无法评论 |
| Redis | ❌ 不需要 | 项目未使用 |
| Node.js 20+ | ✅ **必需** | 前端 + 管理后台构建和运行 |
| Python 3.10+ | ✅ **必需** | 后端运行 |

### 2.2 ⚠️ 部署前必须修改的配置

**1) `Kirameku/siteConfig.ts` — 将 `apiBaseUrl` 改为空字符串：**

```typescript
// ✅ 正确：留空，让 Next.js rewrites + Nginx 反代处理
apiBaseUrl: "",

// ❌ 错误：绝对不能写死后端地址
// apiBaseUrl: "http://8.138.17.253:6789"
```

**2) `Kirameku-backend/app/config.py` 第 12 行 — CORS 域名确认：**

```python
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173,https://boke.hiromu.top"
).split(",")
# ↑ 最后一个改成你的实际域名
```

**3) `Kirameku-backend/app/main.py` 第 38 行 — 管理后台静态目录：**

```python
# admin 包默认输出到 dist/，但代码里写的是 build/
# 需要二选一处理（详见 3.3 节）
admin_build = Path(__file__).resolve().parent.parent / "admin" / "build"
```

---

## 三、详细部署步骤

### 3.1 数据库初始化 (MySQL)

在宝塔面板的「数据库」中创建 MySQL 数据库：

```bash
# 方法一：mysql 命令行导入（先创建数据库）
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS kirameku DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci;"
mysql -u root -p kirameku < /www/wwwroot/your-project/Kirameku-backend/init_db.sql

# 方法二：宝塔面板 → 数据库 → MySQL → 添加数据库 → 导入 init_db.sql
```

执行后验证：
```sql
-- 确认表已创建
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'kirameku' ORDER BY table_name;

-- 确认默认管理员已插入
SELECT username, nickname, is_admin FROM `user`;
```

默认管理员账号：`admin` / `admin123`

### 3.2 MinIO 对象存储部署

```bash
# 在项目根目录（有 docker-compose.yml 的位置）
cd /www/wwwroot/your-project

# 启动 MinIO
docker compose up -d minio

# 验证
curl http://127.0.0.1:9000/minio/health/live
```

MinIO 管理控制台：`http://你的服务器IP:9001`（默认账号 `minioadmin` / `minioadmin`）

启动后程序会自动创建 `kirameku` bucket 并设为公开读。

### 3.3 后端部署 (FastAPI)

```bash
# 1. 进入后端目录
cd /www/wwwroot/your-project/Kirameku-backend

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt
# 注意：config.py 用了 dotenv，但 requirements.txt 漏了
pip install python-dotenv
```

**3.2.1 配置环境变量**

复制并编辑 `.env`：
```bash
cp .env.example .env
vim .env
```

```ini
# ========== 必填 ==========
# MySQL 连接字符串
DATABASE_URL=mysql+pymysql://root:你的数据库密码@127.0.0.1:3306/kirameku?charset=utf8mb4

# JWT 签名密钥（生成方式: openssl rand -hex 32）
SECRET_KEY=你随机生成的长字符串

# CORS 允许的前端域名
CORS_ORIGINS=https://你的域名,http://localhost:3000,http://localhost:5173

# ========== 必填（MinIO 对象存储）==========
MINIO_ENDPOINT=127.0.0.1:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=kirameku
MINIO_SECURE=false
MINIO_PUBLIC_URL=http://你的域名:9000/kirameku

# ========== 可选（GitHub OAuth 评论登录）==========
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
```

**3.2.2 使用 Supervisor 管理进程（推荐）**

不要用 `start.py`（那是本地开发用的），用 Supervisor 管理生产进程：

```bash
# 安装 supervisor
sudo apt install supervisor -y
```

创建配置文件 `/etc/supervisor/conf.d/kirameku-backend.conf`：

```ini
[program:kirameku-backend]
directory=/www/wwwroot/your-project/Kirameku-backend
command=/www/wwwroot/your-project/Kirameku-backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 6789 --workers 2
user=www
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/www/wwwroot/your-project/Kirameku-backend/logs/uvicorn.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=5
environment=PATH="/www/wwwroot/your-project/Kirameku-backend/venv/bin"
```

```bash
# 启动
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start kirameku-backend

# 常用命令
sudo supervisorctl status kirameku-backend
sudo supervisorctl restart kirameku-backend
sudo supervisorctl tail -f kirameku-backend
```

**关键参数说明：**
- `--host 127.0.0.1`：只监听本地，通过 Nginx 反代对外暴露（安全）
- `--workers 2`：1.8GB 内存建议 2 worker，内存充足可设 `cores × 1`
- `app.main:app`：FastAPI 应用入口路径

### 3.4 管理后台构建 (Vue Admin)

```bash
cd /www/wwwroot/your-project/Kirameku-backend/admin

# 安装 pnpm（如果没有）
npm install -g pnpm

# 安装依赖
pnpm install

# 构建生产版本（输出到 dist/ 目录）
pnpm build

# ⚠️ 关键：main.py 期望在 admin/build/ 找到静态文件
# 方案一：创建软链接
ln -s /www/wwwroot/your-project/Kirameku-backend/admin/dist \
      /www/wwwroot/your-project/Kirameku-backend/admin/build

# 方案二：直接移动/重命名
mv dist build

# 方案三：修改 vite.config.ts，添加 build.outDir
# export default defineConfig({
#   build: { outDir: "build" }
# })
```

### 3.5 前端博客构建与运行 (Next.js)

```bash
cd /www/wwwroot/your-project/Kirameku

# 安装 pnpm（如果没有）
npm install -g pnpm

# 安装依赖
pnpm install

# ⚠️ 如果服务器内存 < 2GB，先限制 Node.js 内存
export NODE_OPTIONS="--max-old-space-size=512"

# 检查 siteConfig.ts 的 apiBaseUrl 是否为空字符串
grep "apiBaseUrl" siteConfig.ts
# 应该输出: apiBaseUrl: "",

# 构建生产版本
pnpm build

# 构建产物在 .next/ 目录
```

**用 Supervisor 管理 Next.js 进程：**

创建 `/etc/supervisor/conf.d/kirameku-frontend.conf`：

```ini
[program:kirameku-frontend]
directory=/www/wwwroot/your-project/Kirameku
command=/usr/bin/node /www/wwwroot/your-project/Kirameku/node_modules/.bin/next start
user=www
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/www/wwwroot/your-project/Kirameku/logs/next.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=5
environment=NODE_ENV=production,NODE_OPTIONS="--max-old-space-size=512"

[program:kirameku-backend]
...
```

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start kirameku-frontend
```

### 3.6 宝塔面板 Nginx 配置

在宝塔面板 → 网站 → 对应站点 → 配置文件：

```nginx
server {
    listen 80;
    server_name 你的域名;

    # HTTPS 重定向（如果有 SSL 证书）
    # return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name 你的域名;

    # SSL 证书（宝塔面板自动管理）
    ssl_certificate     /www/server/panel/vhost/cert/你的域名/fullchain.pem;
    ssl_certificate_key /www/server/panel/vhost/cert/你的域名/privkey.pem;

    # ========== API 反代 → FastAPI (6789) ==========
    # 这些 location 必须在 / 之前，匹配优先级更高
    location /api/ {
        proxy_pass http://127.0.0.1:6789;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 上传超时
        client_max_body_size 100m;
        proxy_connect_timeout 30s;
        proxy_read_timeout 60s;
        proxy_send_timeout 30s;
    }

    location /uploads/ {
        proxy_pass http://127.0.0.1:6789;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 100m;
    }

    location /admin/ {
        proxy_pass http://127.0.0.1:6789;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # ========== 前端 SSR → Next.js (3000) ==========
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # ⚠️ 关键：禁用代理缓存，否则部署后返回旧 HTML
        proxy_no_cache 1;
        proxy_cache_bypass 1;
        proxy_cache off;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";

        proxy_connect_timeout 30s;
        proxy_read_timeout 86400s;
        proxy_send_timeout 30s;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # ========== 静态资源缓存 ==========
    location /_next/static/ {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        expires 365d;
        add_header Cache-Control "public, immutable";
    }
}
```

配置完成后重载 Nginx：
```bash
nginx -t          # 检查配置语法
nginx -s reload   # 重载
```

### 3.7 验证部署

```bash
# 1. 后端健康检查
curl http://127.0.0.1:6789/api/health
# 预期输出: {"status":"ok"}

# 2. API 接口
curl http://127.0.0.1:6789/api/posts/count?status=published

# 3. 前端
curl -s http://127.0.0.1:3000 | head -20
# 应该返回 HTML

# 4. Nginx 代理 → 后端
curl https://你的域名/api/health
# 预期输出: {"status":"ok"}

# 5. 确认是最新构建
curl -s https://你的域名/ | grep buildId
```

---

## 四、进程管理总览

部署完成后，你的服务器上应有以下进程：

| 进程 | 管理方式 | 端口 | 命令 |
|------|----------|------|------|
| Nginx | 宝塔面板 | 80/443 | 系统服务 |
| MySQL | 宝塔面板 | 3306 | 系统服务 |
| MinIO | Docker Compose | 9000/9001 | `docker compose up -d minio` |
| Next.js | Supervisor | 3000 | `next start` |
| FastAPI | Supervisor | 6789 | `uvicorn app.main:app --host 127.0.0.1 --port 6789 --workers 2` |

常用运维命令：
```bash
# 查看所有进程状态
sudo supervisorctl status

# 重启后端（部署新代码后）
sudo supervisorctl restart kirameku-backend

# 重启前端（部署新代码后）
cd /www/wwwroot/your-project/Kirameku && pnpm build
sudo supervisorctl restart kirameku-frontend

# 查看后端日志
sudo supervisorctl tail -f kirameku-backend

# 重新部署管理后台
cd /www/wwwroot/your-project/Kirameku-backend/admin && pnpm build
# build → dist/ 已软链到 build/，无需额外操作
```

---

## 五、更新部署流程

日常更新代码后，按以下步骤操作：

```bash
# 1. 拉取新代码
cd /www/wwwroot/your-project
git pull

# 2. 更新后端
cd Kirameku-backend
source venv/bin/activate
pip install -r requirements.txt  # 如有新依赖
sudo supervisorctl restart kirameku-backend

# 3. 更新管理后台（如有变更）
cd admin
pnpm install  # 如有新依赖
pnpm build
# 无需重启（FastAPI 直接读静态文件）

# 4. 更新前端
cd ../../Kirameku
pnpm install  # 如有新依赖
export NODE_OPTIONS="--max-old-space-size=512"
pnpm build
sudo supervisorctl restart kirameku-frontend

# 5. 验证
curl https://你的域名/api/health
curl -s https://你的域名/ | grep buildId
```

---

## 六、注意事项 & 已知问题

### 6.1 关键问题清单

| # | 问题 | 影响 | 解决 |
|---|------|------|------|
| 1 | `requirements.txt` 缺少 `python-dotenv` | 启动报错 `ModuleNotFoundError` | `pip install python-dotenv` |
| 2 | 管理后台构建输出 `dist/` 但 `main.py` 找 `build/` | 后台页面 404 | 创建软链接 `ln -s dist build` |
| 3 | MinIO 未启动 | 上传图片失败 | 确保 docker-compose 中 minio 容器运行中 |
| 4 | Nginx 缓存旧 HTML | 部署后页面白屏/Mixed Content 错误 | `proxy_cache off` + `proxy_no_cache 1` |
| 5 | 1.8GB 内存不足 | Next.js build 时 OOM | `NODE_OPTIONS="--max-old-space-size=512"` |

### 6.2 安全建议

1. **数据库密码**：不要用默认密码，使用强随机密码
2. **SECRET_KEY**：`openssl rand -hex 32` 生成
3. **MinIO AccessKey**：生产环境务必修改默认的 `minioadmin/minioadmin` 账号密码
4. **FastAPI**：只监听 `127.0.0.1`，不暴露公网端口
5. **防火墙**：只开放 80/443/22 端口，关闭 3000/6789/3306 公网访问
6. **管理后台**：`/admin` 路径建议加 Nginx Basic Auth 或 VPN 限制
