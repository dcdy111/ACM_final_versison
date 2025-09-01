from flask import Blueprint, request, jsonify, abort, session
from db_utils import get_db
import os
from datetime import datetime
# 导入Socket.IO通知工具
from socket_utils import notify_team_update

advisor_bp = Blueprint('advisor', __name__)

# 文件上传配置
UPLOAD_FOLDER = 'static/uploads/advisors'
from .utils import allowed_file

@advisor_bp.route('/advisors', methods=['GET'])
def get_advisors():
    """获取所有指导老师"""
    try:
        with get_db() as conn:
            cursor = conn.execute('''
                SELECT * FROM advisors 
                WHERE status = 'active'
                ORDER BY COALESCE(sort_order, 0) ASC, created_at DESC
            ''')
            advisors = cursor.fetchall()
            
            result = []
            for advisor in advisors:
                advisor_dict = dict(advisor)
                result.append(advisor_dict)
            
            return jsonify(result)
    except Exception as e:
        print(f"Error fetching advisors: {e}")
        return jsonify({'error': str(e)}), 500

@advisor_bp.route('/frontend/advisors', methods=['GET'])
def get_frontend_advisors():
    """前端获取指导老师数据"""
    try:
        # 检查是否在 Vercel 环境中
        if os.environ.get('VERCEL'):
            # Vercel 环境：返回Mock数据
            mock_advisors = [
                {
                    'id': 1,
                    'name': '张教授',
                    'position': '计算机科学系主任、博士生导师',
                    'description': '主要研究方向：机器学习、人工智能、计算机视觉。发表SCI论文60余篇，主持国家自然科学基金项目5项。',
                    'image_url': 'https://picsum.photos/300/300?random=101',
                    'email': 'zhang.prof@university.edu.cn',
                    'google_scholar': 'https://scholar.google.com/citations?user=example1',
                    'github': 'https://github.com/zhangprof',
                    'border_color': 'primary',
                    'status': 'active',
                    'sort_order': 1
                },
                {
                    'id': 2,
                    'name': '李教授',
                    'position': '算法实验室主任、教授',
                    'description': '主要研究方向：算法优化、分布式计算、大数据处理。IEEE高级会员，获得国家科技进步二等奖。',
                    'image_url': 'https://picsum.photos/300/300?random=102',
                    'email': 'li.prof@university.edu.cn',
                    'google_scholar': 'https://scholar.google.com/citations?user=example2',
                    'github': 'https://github.com/liprof',
                    'border_color': 'secondary',
                    'status': 'active',
                    'sort_order': 2
                },
                {
                    'id': 3,
                    'name': '王副教授',
                    'position': '数据科学中心副主任',
                    'description': '主要研究方向：深度学习、自然语言处理、推荐系统。发表顶级会议论文30余篇，获得多项发明专利。',
                    'image_url': 'https://picsum.photos/300/300?random=103',
                    'email': 'wang.prof@university.edu.cn',
                    'google_scholar': 'https://scholar.google.com/citations?user=example3',
                    'github': 'https://github.com/wangprof',
                    'border_color': 'accent',
                    'status': 'active',
                    'sort_order': 3
                }
            ]
            print(f"🔧 Vercel环境：返回指导老师Mock数据 {len(mock_advisors)} 位")
            return jsonify(mock_advisors)
        
        # 本地环境：正常数据库查询
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM advisors WHERE status = 'active' ORDER BY sort_order")
            advisors = cursor.fetchall()
            
            # 将数据库行转换为字典列表
            advisors_data = []
            for advisor in advisors:
                advisor_dict = dict(advisor)
                advisors_data.append(advisor_dict)
            
        return jsonify(advisors_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@advisor_bp.route('/advisors/admin', methods=['GET'])
def get_advisors_admin():
    """管理员获取所有指导老师（包括非活跃状态）"""
    try:
        with get_db() as conn:
            cursor = conn.execute('''
                SELECT * FROM advisors 
                ORDER BY COALESCE(sort_order, 0) ASC, created_at DESC
            ''')
            advisors = cursor.fetchall()
            
            result = []
            for advisor in advisors:
                advisor_dict = dict(advisor)
                result.append(advisor_dict)
            
            return jsonify(result)
    except Exception as e:
        print(f"Error fetching advisors (admin): {e}")
        return jsonify({'error': str(e)}), 500

@advisor_bp.route('/advisors', methods=['POST'])
def create_advisor():
    """创建新指导老师"""
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({"error": "未授权"}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据为空"}), 400
        
        name = str(data.get('name', '')).strip()
        position = str(data.get('position', '')).strip()
        description = str(data.get('description', '')).strip()
        image_url = str(data.get('image_url', '')).strip()
        email = str(data.get('email', '')).strip()
        google_scholar = str(data.get('google_scholar', '')).strip()
        github = str(data.get('github', '')).strip()
        border_color = str(data.get('border_color', 'primary')).strip()
        status = str(data.get('status', 'active')).strip()
        
        # 验证必填字段
        if not name:
            return jsonify({"error": "姓名不能为空"}), 400
        
        if not position:
            return jsonify({"error": "职称不能为空"}), 400
        
        with get_db() as conn:
            # 获取最大排序索引
            cursor = conn.execute('SELECT COALESCE(MAX(sort_order), 0) FROM advisors')
            max_order = cursor.fetchone()[0]
            
            # 插入新指导老师
            cursor = conn.execute('''
                INSERT INTO advisors (name, position, description, image_url, email, 
                                   google_scholar, github, border_color, status, sort_order,
                                   created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                name, position, description, image_url, email, google_scholar,
                github, border_color, status, max_order + 1,
                datetime.now().isoformat(), datetime.now().isoformat()
            ))
            
            advisor_id = cursor.lastrowid
            conn.commit()
            
            print(f"✅ 指导老师创建成功: {name}")
            
            # 通知前端刷新
            notify_team_update({'advisor_created': True, 'advisor_id': advisor_id})
            
            return jsonify({
                "success": True,
                "message": "指导老师创建成功",
                "advisor_id": advisor_id
            }), 201
            
    except Exception as e:
        print(f"Error creating advisor: {e}")
        return jsonify({"error": f"创建失败: {str(e)}"}), 500

@advisor_bp.route('/advisors/<int:advisor_id>', methods=['PUT'])
def update_advisor(advisor_id):
    """更新指导老师信息"""
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({"error": "未授权"}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据为空"}), 400
        
        with get_db() as conn:
            # 检查指导老师是否存在
            cursor = conn.execute('SELECT * FROM advisors WHERE id = ?', (advisor_id,))
            if not cursor.fetchone():
                return jsonify({"error": "指导老师不存在"}), 404
            
            # 构建更新字段
            update_fields = []
            update_values = []
            
            # 处理各个字段
            if 'name' in data:
                update_fields.append('name = ?')
                update_values.append(str(data['name']).strip())
            
            if 'position' in data:
                update_fields.append('position = ?')
                update_values.append(str(data['position']).strip())
            
            if 'description' in data:
                update_fields.append('description = ?')
                update_values.append(str(data['description']).strip())
            
            if 'image_url' in data:
                update_fields.append('image_url = ?')
                update_values.append(str(data['image_url']).strip())
            
            if 'email' in data:
                update_fields.append('email = ?')
                update_values.append(str(data['email']).strip())
            
            if 'google_scholar' in data:
                update_fields.append('google_scholar = ?')
                update_values.append(str(data['google_scholar']).strip())
            
            if 'github' in data:
                update_fields.append('github = ?')
                update_values.append(str(data['github']).strip())
            
            if 'border_color' in data:
                update_fields.append('border_color = ?')
                update_values.append(str(data['border_color']).strip())
            
            if 'status' in data:
                update_fields.append('status = ?')
                update_values.append(str(data['status']).strip())
            
            if 'sort_order' in data:
                update_fields.append('sort_order = ?')
                update_values.append(int(data['sort_order']))
            
            # 添加更新时间
            update_fields.append('updated_at = ?')
            update_values.append(datetime.now().isoformat())
            
            # 添加指导老师ID到值列表
            update_values.append(advisor_id)
            
            # 执行更新
            if update_fields:
                sql = f'UPDATE advisors SET {", ".join(update_fields)} WHERE id = ?'
                conn.execute(sql, update_values)
                conn.commit()
                
                print(f"✅ 指导老师更新成功: ID={advisor_id}")
                
                # 通知前端刷新
                notify_team_update({'advisor_updated': True, 'advisor_id': advisor_id})
                
                return jsonify({"success": True, "message": "更新成功"})
            else:
                return jsonify({"error": "没有需要更新的字段"}), 400
                
    except Exception as e:
        print(f"Error updating advisor: {e}")
        return jsonify({"error": f"更新失败: {str(e)}"}), 500

@advisor_bp.route('/advisors/<int:advisor_id>', methods=['DELETE'])
def delete_advisor(advisor_id):
    """删除指导老师"""
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({"error": "未授权"}), 401
    
    try:
        with get_db() as conn:
            # 检查指导老师是否存在
            cursor = conn.execute('SELECT * FROM advisors WHERE id = ?', (advisor_id,))
            advisor = cursor.fetchone()
            if not advisor:
                return jsonify({"error": "指导老师不存在"}), 404
            
            # 删除指导老师
            conn.execute('DELETE FROM advisors WHERE id = ?', (advisor_id,))
            conn.commit()
            
            print(f"✅ 指导老师删除成功: {advisor['name']}")
            
            # 通知前端刷新
            notify_team_update({'advisor_deleted': True, 'advisor_id': advisor_id})
            
            return jsonify({"success": True, "message": "删除成功"})
            
    except Exception as e:
        print(f"Error deleting advisor: {e}")
        return jsonify({"error": f"删除失败: {str(e)}"}), 500

@advisor_bp.route('/advisors/reorder', methods=['POST'])
def reorder_advisors():
    """重新排序指导老师"""
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({"error": "未授权"}), 401
    
    try:
        data = request.get_json()
        if not data or 'advisor_ids' not in data:
            return jsonify({"error": "缺少排序数据"}), 400
        
        advisor_ids = data['advisor_ids']
        if not isinstance(advisor_ids, list):
            return jsonify({"error": "排序数据格式错误"}), 400
        
        with get_db() as conn:
            # 批量更新排序
            for index, advisor_id in enumerate(advisor_ids):
                conn.execute('UPDATE advisors SET sort_order = ? WHERE id = ?', (index + 1, advisor_id))
            
            conn.commit()
            
            print(f"✅ 指导老师排序更新成功，共{len(advisor_ids)}个指导老师")
            
            # 通知前端刷新
            notify_team_update({'advisors_reordered': True, 'advisor_ids': advisor_ids})
            
            return jsonify({"success": True, "message": "排序更新成功"})
            
    except Exception as e:
        print(f"Error reordering advisors: {e}")
        return jsonify({"error": f"排序更新失败: {str(e)}"}), 500

@advisor_bp.route('/advisors/upload-image', methods=['POST'])
def upload_advisor_image():
    """上传指导老师头像"""
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({"error": "未授权"}), 401
    
    try:
        if 'file' not in request.files:
            return jsonify({"error": "未找到上传文件"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "文件名为空"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "不支持的文件类型"}), 400
        
        # 确保上传目录存在
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # 生成安全的文件名
        from werkzeug.utils import secure_filename
        import secrets
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        new_filename = f"advisor_{secrets.token_hex(8)}{ext}"
        file_path = os.path.join(UPLOAD_FOLDER, new_filename)
        
        # 保存文件
        file.save(file_path)
        
        # 返回相对URL
        image_url = f"/static/uploads/advisors/{new_filename}"
        
        print(f"✅ 指导老师头像上传成功: {image_url}")
        
        return jsonify({
            "success": True,
            "message": "头像上传成功",
            "image_url": image_url
        })
        
    except Exception as e:
        print(f"Error uploading advisor image: {e}")
        return jsonify({"error": f"上传失败: {str(e)}"}), 500
