"""
数据库工具模块
用于提供数据库连接功能，避免循环导入问题
"""

import sqlite3
import os
from contextlib import contextmanager

def get_db_path():
    """获取数据库文件路径"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'acm_lab.db')
    return db_path

@contextmanager
def get_db():
    """
    获取数据库连接的上下文管理器
    
    Yields:
        sqlite3.Connection: 数据库连接对象
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
    conn.isolation_level = None  # 启用自动提交模式
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """初始化数据库表结构"""
    with get_db() as conn:
        # 创建用户表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'admin',
                display_name TEXT,
                avatar TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建团队成员表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS team_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                position TEXT,
                description TEXT,
                image_url TEXT,
                qq TEXT,
                wechat TEXT,
                email TEXT,
                group_name TEXT DEFAULT '算法组',
                status TEXT DEFAULT '在职',
                grade TEXT DEFAULT '2024级',
                order_index INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 修复现有团队成员的order_index
        try:
            # 检查是否有order_index为NULL或0的成员
            cursor = conn.execute('''
                SELECT id FROM team_members 
                WHERE order_index IS NULL OR order_index = 0 
                ORDER BY created_at ASC
            ''')
            members_to_fix = cursor.fetchall()
            
            if members_to_fix:
                print(f"🔧 发现 {len(members_to_fix)} 个需要修复order_index的团队成员")
                
                # 获取当前最大order_index
                cursor = conn.execute('SELECT COALESCE(MAX(order_index), 0) FROM team_members')
                max_order = cursor.fetchone()[0]
                
                # 为每个成员设置正确的order_index
                for index, member in enumerate(members_to_fix):
                    new_order = max_order + index + 1
                    conn.execute('''
                        UPDATE team_members 
                        SET order_index = ?, updated_at = CURRENT_TIMESTAMP 
                        WHERE id = ?
                    ''', (new_order, member[0]))
                    print(f"  - 成员ID {member[0]} 设置order_index为 {new_order}")
                
                conn.commit()
                print("✅ 团队成员order_index修复完成")
            else:
                print("✅ 团队成员order_index已正确设置")
        except Exception as e:
            print(f"⚠️ 修复团队成员order_index时出错: {e}")
        
        # 创建年级表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                order_index INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 插入默认年级数据
        default_grades = [
            ('2024级', '2024级年级组', 1),
            ('2023级', '2023级年级组', 2),
            ('2022级', '2022级年级组', 3),
            ('2021级', '2021级年级组', 4),
            ('2020级', '2020级年级组', 5),
            ('2019级', '2019级年级组', 6),
            ('2018级', '2018级年级组', 7),
            ('2017级', '2017级年级组', 8),
            ('2016级', '2016级年级组', 9)
        ]
        
        # 检查是否已经插入过默认数据
        existing_grades = conn.execute('SELECT COUNT(*) FROM grades').fetchone()[0]
        if existing_grades == 0:
            for grade in default_grades:
                conn.execute('''
                    INSERT INTO grades (name, description, order_index)
                    VALUES (?, ?, ?)
                ''', grade)
        
        # 创建研究项目表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS research_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT DEFAULT '深度学习',
                description TEXT,
                members TEXT,
                order_index INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建论文类别表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS paper_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                level INTEGER NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 插入默认的论文类别数据
        default_categories = [
            ('CCF-A', 1, 'CCF推荐会议和期刊A类'),
            ('CCF-B', 2, 'CCF推荐会议和期刊B类'),
            ('CCF-C', 3, 'CCF推荐会议和期刊C类'),
            ('中科院一区', 4, '中科院分区一区'),
            ('中科院二区', 5, '中科院分区二区'),
            ('中科院三区', 6, '中科院分区三区'),
            ('中科院四区', 7, '中科院分区四区'),
            ('JCR一区', 8, 'JCR分区一区'),
            ('JCR二区', 9, 'JCR分区二区'),
            ('JCR三区', 10, 'JCR分区三区'),
            ('JCR四区', 11, 'JCR分区四区'),
            ('EI源刊', 12, 'EI收录的期刊'),
            ('EI会议', 13, 'EI收录的会议'),
            ('南核', 14, '南大核心期刊'),
            ('CSCD', 15, '中国科学引文数据库'),
            ('北核', 16, '北大核心期刊'),
            ('普刊', 17, '普通期刊')
        ]
        
        # 检查是否已经插入过默认数据
        existing_categories = conn.execute('SELECT COUNT(*) FROM paper_categories').fetchone()[0]
        if existing_categories == 0:
            for category in default_categories:
                conn.execute('''
                    INSERT INTO paper_categories (name, level, description)
                    VALUES (?, ?, ?)
                ''', category)
        
        # 创建论文表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                authors TEXT,
                journal TEXT,
                year INTEGER,
                abstract TEXT,
                category_ids TEXT DEFAULT '[]',
                status TEXT DEFAULT 'published',
                order_index INTEGER DEFAULT 0,
                citation_count INTEGER DEFAULT 0,
                doi TEXT,
                pdf_url TEXT,
                code_url TEXT,
                video_url TEXT,
                demo_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建论文类别关联表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS paper_category_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (paper_id) REFERENCES papers (id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES paper_categories (id) ON DELETE CASCADE,
                UNIQUE(paper_id, category_id)
            )
        ''')
        
        # 创建算法表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS algorithms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                time_complexity TEXT,
                space_complexity TEXT,
                code_preview TEXT,
                pdf_url TEXT,
                status TEXT DEFAULT 'active',
                order_index INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建算法竞赛获奖表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS algorithm_awards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                competition_name TEXT NOT NULL,
                award_level TEXT NOT NULL,
                winner_name TEXT,
                competition_date DATE,
                competition_location TEXT,
                team_score TEXT,
                image_url TEXT,
                description TEXT,
                status TEXT DEFAULT 'active',
                order_index INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建项目概览统计表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS project_overview (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                value INTEGER DEFAULT 0,
                icon TEXT,
                description TEXT,
                status TEXT DEFAULT 'active',
                order_index INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建科创项目表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS innovation_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                image_url TEXT,
                category TEXT DEFAULT '国家级创新创业项目',
                tags TEXT,
                detail_url TEXT,
                status TEXT DEFAULT 'active',
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建指导老师表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS advisors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                position TEXT NOT NULL,
                description TEXT,
                image_url TEXT,
                email TEXT,
                google_scholar TEXT,
                github TEXT,
                border_color TEXT DEFAULT 'primary',
                status TEXT DEFAULT 'active',
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建研究领域表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS research_areas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT DEFAULT '深度学习',
                description TEXT,
                members TEXT,
                order_index INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 插入默认研究领域数据
        try:
            cursor = conn.execute('SELECT COUNT(*) FROM research_areas')
            if cursor.fetchone()[0] == 0:
                conn.execute('''
                    INSERT INTO research_areas (title, category, description, order_index)
                    VALUES 
                    ('自然语言处理', '深度学习', '研究自然语言的理解、生成和处理技术', 1),
                    ('计算机视觉', '深度学习', '研究图像和视频的识别、分析和理解', 2),
                    ('机器学习', '深度学习', '研究各种机器学习算法和应用', 3),
                    ('证据理论', '证据理论', '研究不确定性推理和证据融合方法', 4),
                    ('文献计量学', '文献计量', '研究学术文献的统计分析和评价方法', 5)
                ''')
                print("已插入默认研究领域数据")
        except Exception as e:
            print(f"插入研究领域数据时出错: {e}")
        
        # 创建通知表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                raw_content TEXT,
                author TEXT,
                category TEXT DEFAULT '实验室制度',
                tags TEXT,
                excerpt TEXT,
                publish_date DATE,
                word_count INTEGER DEFAULT 0,
                reading_time INTEGER DEFAULT 5,
                status TEXT DEFAULT 'published',
                source_type TEXT DEFAULT 'online',
                source_file TEXT,
                card_style TEXT,
                order_index INTEGER DEFAULT 0,
                view_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建上传文件记录表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS uploaded_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_id INTEGER,
                original_filename TEXT,
                stored_filename TEXT,
                file_size INTEGER,
                upload_status TEXT DEFAULT 'success',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (notification_id) REFERENCES notifications (id) ON DELETE CASCADE
            )
        ''')
        
        # ============ 科创管理相关表 ============
        
        # 创建项目统计表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS innovation_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                value INTEGER DEFAULT 0,
                icon TEXT,
                description TEXT,
                status TEXT DEFAULT 'active',
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建轮播图表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS innovation_carousel (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                image_url TEXT,
                image_file TEXT,
                link_url TEXT,
                text_position TEXT DEFAULT 'bottom-left',
                overlay_opacity REAL DEFAULT 0.3,
                status TEXT DEFAULT 'active',
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建成果与荣誉表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                type TEXT DEFAULT 'award',
                description TEXT,
                date DATE,
                icon TEXT,
                status TEXT DEFAULT 'active',
                extra_data TEXT,
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建大学生创新创业训练计划表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS innovation_training_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT DEFAULT '人工智能',
                progress INTEGER DEFAULT 0,
                start_date DATE,
                end_date DATE,
                budget TEXT,
                leader TEXT,
                members_count INTEGER DEFAULT 0,
                contact_email TEXT,
                contact_phone TEXT,
                contact_wechat TEXT,
                image_url TEXT,
                image_file TEXT,
                status TEXT DEFAULT 'active',
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建知识产权表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS intellectual_properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                type TEXT DEFAULT 'patent',
                category TEXT,
                application_date DATE,
                grant_date DATE,
                patent_number TEXT,
                inventors TEXT,
                image_url TEXT,
                image_file TEXT,
                status TEXT DEFAULT 'active',
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建校企合作表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS enterprise_cooperations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                enterprise_name TEXT NOT NULL,
                category TEXT,
                start_date DATE,
                end_date DATE,
                budget TEXT,
                leader TEXT,
                achievement TEXT,
                enterprise_logo TEXT,
                image_url TEXT,
                image_file TEXT,
                status TEXT DEFAULT 'active',
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 插入默认项目统计数据
        try:
            cursor = conn.execute('SELECT COUNT(*) FROM innovation_stats')
            if cursor.fetchone()[0] == 0:
                conn.execute('''
                    INSERT INTO innovation_stats (name, value, icon, description, status, sort_order)
                    VALUES 
                    ('已完成项目', 25, 'fa-check-circle', '累计完成各类创新项目', 'active', 1),
                    ('获得专利', 8, 'fa-lightbulb-o', '获得发明专利和实用新型专利', 'active', 2),
                    ('发表论文', 15, 'fa-file-text-o', '在核心期刊发表学术论文', 'active', 3),
                    ('获得奖项', 12, 'fa-trophy', '在各类竞赛中获得奖项', 'active', 4)
                ''')
                print("已插入默认项目统计数据")
        except Exception as e:
            print(f"插入项目统计数据时出错: {e}")
        
        # 插入默认轮播图数据
        try:
            cursor = conn.execute('SELECT COUNT(*) FROM innovation_carousel')
            if cursor.fetchone()[0] == 0:
                conn.execute('''
                    INSERT INTO innovation_carousel (title, description, image_url, status, sort_order)
                    VALUES 
                    ('智能视觉分析系统', '基于深度学习的智能视觉分析系统，可应用于安防监控、工业检测等领域', '/static/images/carousel/sample1.jpg', 'active', 1),
                    ('自然语言处理平台', '大规模预训练语言模型，支持多语言理解和生成任务', '/static/images/carousel/sample2.jpg', 'active', 2)
                ''')
                print("已插入默认轮播图数据")
        except Exception as e:
            print(f"插入轮播图数据时出错: {e}")
        
        # 插入默认成果与荣誉数据
        try:
            cursor = conn.execute('SELECT COUNT(*) FROM achievements')
            if cursor.fetchone()[0] == 0:
                conn.execute('''
                    INSERT INTO achievements (title, type, description, date, status, sort_order)
                    VALUES 
                    ('全国大学生创新创业大赛金奖', 'award', '在全国大学生创新创业大赛中获得金奖', '2024-06-15', 'active', 1),
                    ('一种基于深度学习的图像识别方法', 'patent', '获得国家发明专利授权', '2024-03-20', 'active', 2)
                ''')
                print("已插入默认成果与荣誉数据")
        except Exception as e:
            print(f"插入成果与荣誉数据时出错: {e}")
        
        # 插入默认训练计划数据
        try:
            cursor = conn.execute('SELECT COUNT(*) FROM innovation_training_projects')
            if cursor.fetchone()[0] == 0:
                conn.execute('''
                    INSERT INTO innovation_training_projects (title, description, category, progress, leader, status, sort_order)
                    VALUES 
                    ('智能视觉分析系统', '基于深度学习的智能视觉分析系统开发', '人工智能', 85, '李教授', 'active', 1),
                    ('大数据分析平台', '企业级大数据分析平台设计与实现', '大数据', 70, '王教授', 'active', 2)
                ''')
                print("已插入默认训练计划数据")
        except Exception as e:
            print(f"插入训练计划数据时出错: {e}")
        
        # 插入默认知识产权数据
        try:
            cursor = conn.execute('SELECT COUNT(*) FROM intellectual_properties')
            if cursor.fetchone()[0] == 0:
                conn.execute('''
                    INSERT INTO intellectual_properties (title, description, type, category, inventors, status, sort_order)
                    VALUES 
                    ('一种基于深度学习的图像识别方法', '利用卷积神经网络进行图像特征提取和分类的方法', 'patent', '人工智能', '张三、李四', 'active', 1),
                    ('智能语音识别系统软件', '基于机器学习的语音识别和转换系统', 'copyright', '人工智能', '王五、赵六', 'active', 2)
                ''')
                print("已插入默认知识产权数据")
        except Exception as e:
            print(f"插入知识产权数据时出错: {e}")
        
        # 插入默认校企合作数据
        try:
            cursor = conn.execute('SELECT COUNT(*) FROM enterprise_cooperations')
            if cursor.fetchone()[0] == 0:
                conn.execute('''
                    INSERT INTO enterprise_cooperations (title, description, enterprise_name, category, leader, status, sort_order)
                    VALUES 
                    ('AI算法优化与芯片适配', '为华为提供AI算法优化和芯片适配服务', '华为技术', '技术研发', '陈教授', 'active', 1),
                    ('大数据分析平台开发', '为腾讯开发企业级大数据分析平台', '腾讯科技', '软件开发', '刘教授', 'active', 2)
                ''')
                print("已插入默认校企合作数据")
        except Exception as e:
            print(f"插入校企合作数据时出错: {e}")
        
        # 检查并添加缺失的字段
        try:
            conn.execute('SELECT created_at FROM team_members LIMIT 1')
        except sqlite3.OperationalError:
            conn.execute('ALTER TABLE team_members ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            print("已添加created_at字段到team_members表")
        
        try:
            conn.execute('SELECT updated_at FROM team_members LIMIT 1')
        except sqlite3.OperationalError:
            conn.execute('ALTER TABLE team_members ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            print("已添加updated_at字段到team_members表")
        
        # 插入示例算法数据
        try:
            # 检查是否已有数据
            cursor = conn.execute('SELECT COUNT(*) FROM algorithms')
            if cursor.fetchone()[0] == 0:
                conn.execute('''
                    INSERT INTO algorithms (title, category, description, time_complexity, space_complexity, code_preview, status, order_index)
                    VALUES 
                    ('快速排序', '基础算法', '一种高效的排序算法，使用分治策略', 'O(n log n)', 'O(log n)', 'def quicksort(arr):\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quicksort(left) + middle + quicksort(right)', 'active', 1),
                    ('动态规划 - 背包问题', '动态规划', '经典的0-1背包问题解决方案', 'O(nW)', 'O(nW)', 'def knapsack(values, weights, W):\n    n = len(values)\n    dp = [[0] * (W + 1) for _ in range(n + 1)]\n    for i in range(1, n + 1):\n        for w in range(W + 1):\n            if weights[i-1] <= w:\n                dp[i][w] = max(dp[i-1][w], dp[i-1][w-weights[i-1]] + values[i-1])\n            else:\n                dp[i][w] = dp[i-1][w]\n    return dp[n][W]', 'active', 2),
                    ('二叉树遍历', '数据结构', '二叉树的前序、中序、后序遍历', 'O(n)', 'O(h)', 'class TreeNode:\n    def __init__(self, val=0):\n        self.val = val\n        self.left = None\n        self.right = None\n\ndef inorder_traversal(root):\n    if root:\n        inorder_traversal(root.left)\n        print(root.val)\n        inorder_traversal(root.right)', 'active', 3)
                ''')
                print("已插入示例算法数据")
        except Exception as e:
            print(f"插入算法数据时出错: {e}")
        
        # 插入示例获奖记录数据
        try:
            cursor = conn.execute('SELECT COUNT(*) FROM algorithm_awards')
            if cursor.fetchone()[0] == 0:
                conn.execute('''
                    INSERT INTO algorithm_awards (title, competition_name, award_level, winner_name, competition_date, competition_location, team_score, description, status, order_index)
                    VALUES 
                    ('ACM-ICPC亚洲区域赛', 'ACM-ICPC Asia Regional Contest', '一等奖', '张三、李四、王五', '2023-10-15', '北京', '95.5分', '在激烈的竞争中脱颖而出，展现了优秀的算法设计和编程能力', 'active', 1),
                    ('蓝桥杯全国总决赛', '蓝桥杯全国软件和信息技术专业人才大赛', '特等奖', '赵六', '2023-05-20', '杭州', '98分', '在全国总决赛中获得特等奖，展现了扎实的编程基础和创新能力', 'active', 2),
                    ('CCPC大学生程序设计竞赛', '中国大学生程序设计竞赛', '二等奖', '钱七、孙八', '2023-09-10', '上海', '88分', '在CCPC竞赛中获得二等奖，体现了良好的团队协作能力', 'active', 3)
                ''')
                print("已插入示例获奖记录数据")
        except Exception as e:
            print(f"插入获奖记录数据时出错: {e}")
        
        # 插入示例项目概览数据
        try:
            cursor = conn.execute('SELECT COUNT(*) FROM project_overview')
            if cursor.fetchone()[0] == 0:
                conn.execute('''
                    INSERT INTO project_overview (name, value, icon, description, status, order_index)
                    VALUES 
                    ('算法总数', 50, 'fa-code', '实验室掌握的算法数量', 'active', 1),
                    ('竞赛获奖', 15, 'fa-trophy', '各类算法竞赛获奖次数', 'active', 2),
                    ('项目完成', 25, 'fa-project-diagram', '完成的算法相关项目数量', 'active', 3),
                    ('团队成员', 12, 'fa-users', '实验室核心成员数量', 'active', 4)
                ''')
                print("已插入示例项目概览数据")
        except Exception as e:
            print(f"插入项目概览数据时出错: {e}")
        
        conn.commit()
        print("数据库初始化完成") 