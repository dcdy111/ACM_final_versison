from flask import Blueprint, request, jsonify, abort, session
from db_utils import get_db
import os
from socket_utils import notify_page_refresh
from datetime import datetime
from .utils import allowed_file

innovation_project_bp = Blueprint('innovation_project', __name__)

# 文件上传配置
UPLOAD_FOLDER = 'static/uploads/innovation_projects'

@innovation_project_bp.route('/api/innovation-projects', methods=['GET'])
def get_innovation_projects():
    """获取所有科创成果"""
    try:
        with get_db() as conn:
            cursor = conn.execute('''
                SELECT * FROM innovation_projects 
                WHERE status = 'active'
                ORDER BY COALESCE(sort_order, 0) ASC, created_at DESC
            ''')
            projects = cursor.fetchall()
            
            result = []
            for project in projects:
                project_dict = dict(project)
                result.append(project_dict)
            
            return jsonify(result)
    except Exception as e:
        print(f"Error fetching innovation projects: {e}")
        return jsonify({'error': str(e)}), 500

@innovation_project_bp.route('/api/innovation-projects/admin', methods=['GET'])
def get_innovation_projects_admin():
    """管理员获取所有科创成果（包括非活跃状态）"""
    try:
        with get_db() as conn:
            cursor = conn.execute('''
                SELECT * FROM innovation_projects 
                ORDER BY COALESCE(sort_order, 0) ASC, created_at DESC
            ''')
            projects = cursor.fetchall()
            
            result = []
            for project in projects:
                project_dict = dict(project)
                result.append(project_dict)
            
            return jsonify(result)
    except Exception as e:
        print(f"Error fetching innovation projects (admin): {e}")
        return jsonify({'error': str(e)}), 500

@innovation_project_bp.route('/api/innovation-projects', methods=['POST'])
def create_innovation_project():
    """创建新科创成果"""
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({"error": "未授权"}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据为空"}), 400
        
        title = str(data.get('title', '')).strip()
        description = str(data.get('description', '')).strip()
        category = str(data.get('category', '')).strip()
        image_url = str(data.get('image_url', '')).strip()
        detail_url = str(data.get('detail_url', '')).strip()  # 修正字段名
        tags = str(data.get('tags', '')).strip()  # 添加tags字段
        status = str(data.get('status', 'active')).strip()
        
        # 验证必填字段
        if not title:
            return jsonify({"error": "项目标题不能为空"}), 400
        
        if not category:
            category = '国家级创新创业项目'  # 设置默认类别
        
        with get_db() as conn:
            # 获取最大排序索引
            cursor = conn.execute('SELECT COALESCE(MAX(sort_order), 0) FROM innovation_projects')
            max_order = cursor.fetchone()[0]
            
            # 插入新项目
            cursor = conn.execute('''
                INSERT INTO innovation_projects (title, description, category, image_url, 
                                              detail_url, tags, status, sort_order,
                                              created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                title, description, category, image_url, detail_url,
                tags, status, max_order + 1,
                datetime.now().isoformat(), datetime.now().isoformat()
            ))
            
            project_id = cursor.lastrowid
            conn.commit()
            
            print(f"✅ 科创成果创建成功: {title}")
            
            # 通知前端刷新
            notify_page_refresh('innovation', {'action': 'created', 'project_id': project_id})
            
            return jsonify({
                "success": True,
                "message": "科创成果创建成功",
                "project_id": project_id
            }), 201
            
    except Exception as e:
        print(f"Error creating innovation project: {e}")
        return jsonify({"error": f"创建失败: {str(e)}"}), 500

@innovation_project_bp.route('/api/innovation-projects/<int:project_id>', methods=['PUT'])
def update_innovation_project(project_id):
    """更新科创成果"""
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({"error": "未授权"}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据为空"}), 400
        
        with get_db() as conn:
            # 检查项目是否存在
            cursor = conn.execute('SELECT * FROM innovation_projects WHERE id = ?', (project_id,))
            if not cursor.fetchone():
                return jsonify({"error": "科创成果不存在"}), 404
            
            # 构建更新字段
            update_fields = []
            update_values = []
            
            # 处理各个字段
            if 'title' in data:
                update_fields.append('title = ?')
                update_values.append(str(data['title']).strip())
            
            if 'description' in data:
                update_fields.append('description = ?')
                update_values.append(str(data['description']).strip())
            
            if 'category' in data:
                update_fields.append('category = ?')
                update_values.append(str(data['category']).strip())
            
            if 'image_url' in data:
                update_fields.append('image_url = ?')
                update_values.append(str(data['image_url']).strip())
            
            if 'detail_url' in data:  # 修正字段名
                update_fields.append('detail_url = ?')
                update_values.append(str(data['detail_url']).strip())
            
            if 'tags' in data:  # 添加tags字段
                update_fields.append('tags = ?')
                update_values.append(str(data['tags']).strip())
            
            if 'status' in data:
                update_fields.append('status = ?')
                update_values.append(str(data['status']).strip())
            
            if 'sort_order' in data:
                update_fields.append('sort_order = ?')
                update_values.append(int(data['sort_order']))
            
            # 添加更新时间
            update_fields.append('updated_at = ?')
            update_values.append(datetime.now().isoformat())
            
            # 添加项目ID到值列表
            update_values.append(project_id)
            
            # 执行更新
            if update_fields:
                sql = f'UPDATE innovation_projects SET {", ".join(update_fields)} WHERE id = ?'
                conn.execute(sql, update_values)
                conn.commit()
                
                print(f"✅ 科创成果更新成功: ID={project_id}")
                
                # 通知前端刷新
                notify_page_refresh('innovation', {'action': 'updated', 'project_id': project_id})
                
                return jsonify({"success": True, "message": "更新成功"})
            else:
                return jsonify({"error": "没有需要更新的字段"}), 400
                
    except Exception as e:
        print(f"Error updating innovation project: {e}")
        return jsonify({"error": f"更新失败: {str(e)}"}), 500

@innovation_project_bp.route('/api/innovation-projects/<int:project_id>', methods=['DELETE'])
def delete_innovation_project(project_id):
    """删除科创成果"""
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({"error": "未授权"}), 401
    
    try:
        with get_db() as conn:
            # 检查项目是否存在
            cursor = conn.execute('SELECT * FROM innovation_projects WHERE id = ?', (project_id,))
            project = cursor.fetchone()
            if not project:
                return jsonify({"error": "科创成果不存在"}), 404
            
            # 删除项目
            conn.execute('DELETE FROM innovation_projects WHERE id = ?', (project_id,))
            conn.commit()
            
            print(f"✅ 科创成果删除成功: {project['title']}")
            
            # 通知前端刷新
            notify_page_refresh('innovation', {'action': 'deleted', 'project_id': project_id})
            
            return jsonify({"success": True, "message": "删除成功"})
            
    except Exception as e:
        print(f"Error deleting innovation project: {e}")
        return jsonify({"error": f"删除失败: {str(e)}"}), 500

@innovation_project_bp.route('/api/innovation-projects/reorder', methods=['POST'])
def reorder_innovation_projects():
    """重新排序科创成果"""
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({"error": "未授权"}), 401
    
    try:
        data = request.get_json()
        if not data or 'project_ids' not in data:
            return jsonify({"error": "缺少排序数据"}), 400
        
        project_ids = data['project_ids']
        if not isinstance(project_ids, list):
            return jsonify({"error": "排序数据格式错误"}), 400
        
        with get_db() as conn:
            # 批量更新排序
            for index, project_id in enumerate(project_ids):
                conn.execute('UPDATE innovation_projects SET sort_order = ? WHERE id = ?', (index + 1, project_id))
            
            conn.commit()
            
            print(f"✅ 科创成果排序更新成功，共{len(project_ids)}个项目")
            
            # 通知前端刷新
            notify_page_refresh('innovation', {'action': 'reordered', 'project_ids': project_ids})
            
            return jsonify({"success": True, "message": "排序更新成功"})
            
    except Exception as e:
        print(f"Error reordering innovation projects: {e}")
        return jsonify({"error": f"排序更新失败: {str(e)}"}), 500

@innovation_project_bp.route('/api/innovation-projects/upload-image', methods=['POST'])
def upload_project_image():
    """上传项目图片"""
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({"error": "未授权"}), 401
    
    if 'file' not in request.files:  # 修正字段名
        return jsonify({"error": "未找到上传文件"}), 400
    
    file = request.files['file']  # 修正字段名
    if file.filename == '':
        return jsonify({"error": "文件名为空"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": "不支持的文件类型"}), 400

    try:
        # 确保上传目录存在
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # 生成安全的文件名
        from werkzeug.utils import secure_filename
        import secrets
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        new_filename = f"project_{secrets.token_hex(8)}{ext}"
        save_path = os.path.join(UPLOAD_FOLDER, new_filename)
        
        # 保存文件
        file.save(save_path)
        
        # 返回相对URL
        rel_url = f"/static/uploads/innovation_projects/{new_filename}"
        
        print(f"✅ 项目图片上传成功: {rel_url}")
        
        return jsonify({
            "success": True, 
            "image_url": rel_url,
            "message": "图片上传成功"
        })
    except Exception as e:
        print(f"Error uploading project image: {e}")
        return jsonify({"error": f"图片上传失败: {str(e)}"}), 500 