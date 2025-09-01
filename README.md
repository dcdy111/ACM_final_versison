# ACM算法研究实验室管理系统

一个功能完整的基于 Flask 的实验室官网与后台管理系统，支持团队成员管理、论文展示、科创项目管理、实时统计等功能。

## 🚀 功能特性

### 前台展示功能
- ✅ **实验室官网首页** - 展示实验室概况、最新动态、研究成果
- ✅ **团队成员展示** - 展示实验室成员信息、研究方向、联系方式
- ✅ **论文成果展示** - 展示实验室发表的学术论文和研究成果
- ✅ **科创成果展示** - 展示实验室的科技创新项目和成果
- ✅ **动态资讯** - 实验室最新动态、通知公告、活动信息
- ✅ **实验室介绍** - 实验室概况、章程、研究方向详细介绍
- ✅ **项目团队招募** - 展示招募信息和申请流程
- ✅ **算法组招募** - 专门的算法组招募页面

### 后台管理功能
- ✅ **用户管理** - 管理员账户管理、权限控制
- ✅ **内容管理** - 团队成员、论文、通知、活动等内容管理
- ✅ **文件上传** - 支持图片、文档（PDF、Word、Markdown）上传
- ✅ **实时更新** - WebSocket实时数据推送，无需刷新页面
- ✅ **访问统计** - 详细的访问数据统计和分析
- ✅ **数据备份** - 自动数据备份和恢复功能
- ✅ **系统监控** - 程序运行状态、网络时间同步

### 技术特性
- ✅ **响应式设计** - 支持PC和移动端访问
- ✅ **实时通信** - WebSocket实时数据推送
- ✅ **数据缓存** - 智能缓存机制提升性能
- ✅ **文件管理** - 支持多种文档格式上传和管理
- ✅ **统计分析** - 详细的访问数据统计和分析
- ✅ **安全认证** - 安全的用户认证和权限管理

## 🛠️ 安装和运行

### 1. 环境准备
确保您的系统已安装：
- Python 3.8 或更高版本
- pip 包管理器

### 2. 下载项目
```bash
git clone <项目地址>
cd acm_lab_ai_make
```

### 3. 创建虚拟环境
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python -m venv .venv
source .venv/bin/activate
```

### 4. 安装依赖
```bash
pip install -r requirements.txt
```

### 5. 启动应用
```bash
python app.py
```

### 6. 访问系统
- **前台官网**: http://127.0.0.1:5000
- **后台管理**: http://127.0.0.1:5000/admin
- **默认账号**: admin / admin123

## 📁 项目结构

```
acm_lab_ai_make/
├── app.py                 # Flask 主应用
├── db_utils.py           # 数据库工具模块
├── socket_utils.py       # WebSocket工具模块
├── db_backup.py          # 数据库备份工具
# 访问统计系统已移除
├── requirements.txt      # 项目依赖
├── acm_lab.db           # SQLite数据库文件
├── templates/           # 模板文件
│   ├── frontend/        # 前台页面模板
│   └── admin/          # 后台管理模板
├── static/             # 静态资源文件
├── api/               # API接口模块
│   # 访问统计系统已移除
│   ├── notifications.py # 通知管理API
│   ├── team.py        # 团队管理API
│   └── innovation.py  # 科创项目API
├── models/            # 数据模型
│   # 访问统计系统已移除
│   ├── team_member.py # 团队成员模型
│   ├── innovation.py  # 科创项目模型
│   └── ...
├── backups/           # 数据备份目录
# 访问统计系统已移除
└── instance/         # 实例配置目录
```

## 🗄️ 数据库设计

系统使用 SQLite 数据库，包含以下主要表：

- **users** - 用户管理表
- **team_members** - 团队成员表
- **papers** - 论文成果表
- **innovation_projects** - 科创项目表
- **notifications** - 通知公告表
- **team_leaders** - 团队领导表
- **algorithms** - 算法展示表
- **visit_records** - 访问记录表
- **site_statistics** - 站点统计表
- **program_run_records** - 程序运行记录表

## 🔧 配置说明

### 环境变量
- `FLASK_DEBUG` - 调试模式开关（默认：True）
- `FLASK_ENV` - 运行环境（development/production）

### 文件上传配置
- 支持的文件类型：图片（jpg, png, gif）、文档（pdf, doc, docx, md）
- 上传目录：`static/uploads/`
- 文件大小限制：16MB

## 📊 系统监控

系统提供以下监控功能：
- **程序运行记录** - 记录程序启动和停止时间
- **访问统计** - 详细的页面访问记录和用户行为分析
- **系统资源监控** - CPU、内存使用情况
- **网络时间同步** - 自动同步网络时间确保数据准确性

## 🔄 数据备份

系统提供自动备份功能：
```bash
# 手动备份数据库
python db_backup.py

# 手动备份统计数据
# 访问统计系统已移除
```

## 🚀 部署说明

### 开发环境
```bash
python app.py
```

### 生产环境
建议使用 Gunicorn 或 uWSGI 部署：
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 📞 技术支持

如遇到问题，请检查：
1. Python版本是否符合要求（3.8+）
2. 虚拟环境是否正确激活
3. 依赖包是否完整安装
4. 端口是否被占用
5. 文件权限是否正确设置

## �� 许可证

MIT License 