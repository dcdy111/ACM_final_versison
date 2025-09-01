# ACM算法研究实验室管理系统 - 详细安装指南

## 🚀 快速开始

### 1. 环境准备
确保您的系统已安装：
- **Python 3.8** 或更高版本
- **pip** 包管理器
- **Git**（用于克隆项目）

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

## 📋 依赖包详细说明

### 核心Web框架
- `Flask==2.3.3` - 轻量级Web框架，提供路由和请求处理
- `Flask-SocketIO==5.3.6` - WebSocket支持，实现实时通信
- `Werkzeug==2.3.7` - WSGI工具库，Flask的依赖
- `flask-sqlalchemy==3.0.5` - SQLAlchemy ORM集成

### 文档处理
- `markdown==3.5.1` - Markdown文档解析和渲染

### 系统监控和性能
- `psutil==5.9.6` - 系统资源监控（CPU、内存、磁盘等）
- `requests==2.31.0` - HTTP请求库，用于网络时间同步

### 文件处理
- `python-multipart==0.0.6` - 文件上传处理

## 🎯 系统功能详解

### 前台展示功能
- **实验室官网首页** - 展示实验室概况、最新动态、研究成果
- **团队成员展示** - 展示实验室成员信息、研究方向、联系方式
- **论文成果展示** - 展示实验室发表的学术论文和研究成果
- **科创成果展示** - 展示实验室的科技创新项目和成果
- **动态资讯** - 实验室最新动态、通知公告、活动信息
- **实验室介绍** - 实验室概况、章程、研究方向详细介绍
- **项目团队招募** - 展示招募信息和申请流程
- **算法组招募** - 专门的算法组招募页面

### 后台管理功能
- **用户管理** - 管理员账户管理、权限控制
- **内容管理** - 团队成员、论文、通知、活动等内容管理
- **文件上传** - 支持图片、文档（PDF、Word、Markdown）上传
- **实时更新** - WebSocket实时数据推送，无需刷新页面
- **访问统计** - 详细的访问数据统计和分析
- **数据备份** - 自动数据备份和恢复功能
- **系统监控** - 程序运行状态、网络时间同步

## 🔧 常见问题解决

### Q: 安装依赖时出错？
**解决方案：**
```bash
# 升级pip
pip install --upgrade pip

# 强制重新安装
pip install -r requirements.txt --force-reinstall

# 如果仍有问题，尝试逐个安装
pip install Flask==2.3.3
pip install Flask-SocketIO==5.3.6
pip install flask-sqlalchemy==3.0.5
pip install Werkzeug==2.3.7
pip install markdown==3.5.1
pip install psutil==5.9.6
pip install requests==2.31.0
pip install python-multipart==0.0.6
```

### Q: 启动时端口被占用？
**解决方案：**
修改 `app.py` 文件中的端口号：
```python
# 找到这一行
socketio.run(app, debug=debug_mode, host='0.0.0.0', port=5000, use_reloader=False)

# 改为其他端口，例如：
socketio.run(app, debug=debug_mode, host='0.0.0.0', port=5001, use_reloader=False)
```

### Q: 数据库文件不存在？
**解决方案：**
- 首次运行会自动创建数据库
- 如果出错，检查目录权限
- 手动创建数据库：
```bash
python -c "from db_utils import init_db; init_db()"
```

### Q: 静态文件无法加载？
**解决方案：**
- 确保 `static` 目录存在
- 检查目录权限
- 确保包含必要的CSS/JS文件

### Q: WebSocket连接失败？
**解决方案：**
- 检查防火墙设置
- 确保WebSocket端口（默认5000）未被阻止
- 检查浏览器是否支持WebSocket

### Q: 文件上传失败？
**解决方案：**
- 检查 `uploads` 目录权限
- 确保应用有写入权限
- 检查文件大小是否超过限制（16MB）

### Q: 访问统计功能异常？
**解决方案：**
- 检查网络连接（用于时间同步）
- 访问统计系统已移除
- 检查数据库连接

## 📊 系统监控功能

### 程序运行监控
- **启动记录** - 记录程序启动时间和环境信息
- **停止记录** - 记录程序停止时间和运行时长
- **异常监控** - 监控程序运行异常和错误

### 访问统计分析
- **页面访问统计** - 记录每个页面的访问次数
- **用户行为分析** - 分析用户访问路径和停留时间
- **实时数据推送** - WebSocket实时推送访问数据

### 系统资源监控
- **CPU使用率** - 实时监控CPU使用情况
- **内存使用率** - 监控内存占用情况
- **磁盘使用情况** - 监控磁盘空间使用

### 网络时间同步
- **多API时间同步** - 使用多个时间API确保准确性
- **自动重试机制** - 网络异常时自动重试
- **本地时间校准** - 校准本地时间与网络时间

## 🔄 数据备份功能

### 自动备份
系统提供自动备份功能，包括：
- **数据库备份** - 定期备份SQLite数据库
- **统计数据备份** - 备份访问统计数据
- **文件备份** - 备份上传的文件

### 手动备份
```bash
# 手动备份数据库
python db_backup.py

# 访问统计系统已移除
```

### 备份恢复
```bash
# 恢复数据库备份
python db_backup.py --restore

# 访问统计系统已移除
```

## 🚀 部署指南

### 开发环境部署
```bash
# 直接运行
python app.py

# 或使用Flask开发服务器
export FLASK_APP=app.py
export FLASK_DEBUG=1
flask run
```

### 生产环境部署
推荐使用 Gunicorn 或 uWSGI：

```bash
# 安装Gunicorn
pip install gunicorn

# 启动服务
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# 或使用uWSGI
pip install uwsgi
uwsgi --http :5000 --wsgi-file app.py --callable app
```

### Docker部署
```dockerfile
FROM python:3.8-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

## 📞 技术支持

### 问题排查步骤
1. **检查Python版本** - 确保使用Python 3.8+
2. **检查虚拟环境** - 确保虚拟环境正确激活
3. **检查依赖安装** - 确保所有依赖包完整安装
4. **检查端口占用** - 确保端口未被其他程序占用
5. **检查文件权限** - 确保应用有必要的文件读写权限
6. **检查网络连接** - 确保网络连接正常（用于时间同步）

### 日志查看
- 应用日志会输出到控制台
- 数据库操作日志在 `acm_lab.db` 中
- 访问统计系统已移除

### 联系支持
如遇到无法解决的问题，请提供以下信息：
- Python版本
- 操作系统版本
- 错误日志
- 复现步骤

更多详细信息请参考 `README.md` 文档。 