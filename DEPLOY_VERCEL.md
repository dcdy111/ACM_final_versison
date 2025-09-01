# Vercel 部署指南

本文档介绍如何将 ACM 实验室管理系统部署到 Vercel 平台。

## 前置要求

1. GitHub 账户
2. Vercel 账户（可使用 GitHub 登录）
3. 项目代码已推送到 GitHub 仓库

## 部署步骤

### 1. 准备项目

确保项目根目录包含以下配置文件：
- `vercel.json` - Vercel 配置文件
- `requirements.txt` - Python 依赖列表
- `.vercelignore` - 忽略文件配置
- `api/index.py` - Vercel 入口文件

### 2. 连接 GitHub 仓库

1. 访问 [Vercel Dashboard](https://vercel.com/dashboard)
2. 点击 "New Project"
3. 选择你的 GitHub 仓库
4. 点击 "Import"

### 3. 配置部署设置

Vercel 会自动检测到这是一个 Python 项目：

- **Framework Preset**: Other
- **Build Command**: 留空（Vercel 会自动处理）
- **Output Directory**: 留空
- **Install Command**: `pip install -r requirements.txt`

### 4. 环境变量配置（可选）

如果需要配置环境变量：
1. 在 Vercel Dashboard 中进入项目设置
2. 选择 "Environment Variables"
3. 添加需要的环境变量，如：
   - `FLASK_ENV=production`
   - `DATABASE_URL=your_database_url`

### 5. 部署

1. 点击 "Deploy" 按钮
2. 等待部署完成（通常需要 1-3 分钟）
3. 部署成功后会显示项目 URL

## 项目结构说明

```
ACM_final/
├── api/
│   └── index.py          # Vercel 入口文件
├── static/               # 静态文件
├── templates/           # HTML 模板
├── acm_lab.py          # 主应用文件
├── vercel.json         # Vercel 配置
├── requirements.txt    # Python 依赖
└── .vercelignore      # 忽略文件
```

## 配置文件说明

### vercel.json
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/index.py"
    }
  ]
}
```

### api/index.py
这是 Vercel 的入口文件，它导入并运行主应用：
```python
from acm_lab import app

if __name__ == "__main__":
    app.run()
```

## 常见问题

### 1. 部署失败
- 检查 `requirements.txt` 中的依赖是否兼容 Vercel
- 确保 `api/index.py` 正确导入主应用
- 查看 Vercel 构建日志中的错误信息

### 2. 静态文件无法访问
- 确保静态文件在 `static/` 目录下
- 检查 Flask 应用中的静态文件配置

### 3. 数据库连接问题
- Vercel 函数是无状态的，不支持持久化的 SQLite 文件
- 考虑使用外部数据库服务（如 PostgreSQL、MySQL）

### 4. 性能优化
- Vercel 函数有冷启动时间
- 考虑使用边缘函数优化响应时间
- 优化 Python 代码以减少启动时间

## 自动部署

连接 GitHub 后，每次推送到主分支都会自动触发部署：
1. 推送代码到 GitHub
2. Vercel 自动检测更改
3. 重新构建和部署
4. 生成新的部署 URL

## 域名配置

### 使用自定义域名：
1. 在 Vercel Dashboard 进入项目设置
2. 选择 "Domains"
3. 添加你的域名
4. 按照说明配置 DNS 记录

## 监控和日志

- 在 Vercel Dashboard 中查看部署历史
- 监控函数执行时间和错误
- 查看实时日志和分析数据

## 限制说明

Vercel 免费版限制：
- 函数执行时间：10 秒
- 函数大小：50MB
- 带宽：100GB/月
- 部署次数：无限制

## 故障排除

1. **构建失败**：检查依赖兼容性和 Python 版本
2. **运行时错误**：查看函数日志，检查代码逻辑
3. **超时问题**：优化代码性能，减少执行时间
4. **内存不足**：减少内存使用，优化数据处理

## 支持

如遇到问题：
1. 查看 [Vercel 官方文档](https://vercel.com/docs)
2. 检查项目的 GitHub Issues
3. 联系开发团队

---

**注意**：部署前请确保在本地环境中测试应用正常运行。
