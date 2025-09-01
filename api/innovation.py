from flask import Blueprint, request, jsonify, abort, current_app
from db_utils import get_db
from datetime import datetime
from socket_utils import notify_page_refresh
from .utils import allowed_file, ensure_upload_dir
import json

innovation_bp = Blueprint('innovation', __name__, url_prefix='/api/innovation')

# ============ 项目统计管理 ============

@innovation_bp.route('/stats', methods=['GET'])
def get_stats():
    """获取项目统计列表"""
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM innovation_stats ORDER BY sort_order ASC")
            stats = cursor.fetchall()
            
            result = []
            for stat in stats:
                stat_dict = dict(stat)
                result.append(stat_dict)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/stats', methods=['POST'])
def create_stats():
    """创建项目统计"""
    try:
        data = request.json
        
        # 获取最大排序值
        max_sort = 0  # 简化处理，使用默认值
        
        with get_db() as conn:
            # 插入新记录
            cursor = conn.execute(
                "INSERT INTO innovation_stats (name, value, icon, description, status, sort_order, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    data.get('name'),
                    data.get('value', 0),
                    data.get('icon'),
                    data.get('description'),
                    data.get('status', 'active'),
                    max_sort + 1,
                    datetime.now(),
                    datetime.now()
                )
            )
            conn.commit()
            
            # 获取新创建的记录
            cursor = conn.execute("SELECT * FROM innovation_stats WHERE id = ?", (cursor.lastrowid,))
            new_stat = cursor.fetchone()
            
            if new_stat:
                return jsonify(dict(new_stat)), 201
            else:
                return jsonify({'error': '创建失败'}), 500
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/stats/<int:stats_id>', methods=['PUT'])
def update_stats(stats_id):
    """更新项目统计"""
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM innovation_stats WHERE id = ?", (stats_id,))
            stats = cursor.fetchone()
            if not stats:
                abort(404)
            
            data = request.json
            
            # 更新记录
            conn.execute(
                "UPDATE innovation_stats SET name = ?, value = ?, icon = ?, description = ?, status = ?, updated_at = ? WHERE id = ?",
                (
                    data.get('name', stats['name']),
                    data.get('value', stats['value']),
                    data.get('icon', stats['icon']),
                    data.get('description', stats['description']),
                    data.get('status', stats['status']),
                    datetime.now(),
                    stats_id
                )
            )
            conn.commit()
            
            # 获取更新后的记录
            cursor = conn.execute("SELECT * FROM innovation_stats WHERE id = ?", (stats_id,))
            updated_stat = cursor.fetchone()
            
            return jsonify(dict(updated_stat))
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/stats/<int:stats_id>', methods=['DELETE'])
def delete_stats(stats_id):
    """删除项目统计"""
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM innovation_stats WHERE id = ?", (stats_id,))
            stats = cursor.fetchone()
            if not stats:
                abort(404)
            
            conn.execute("DELETE FROM innovation_stats WHERE id = ?", (stats_id,))
            conn.commit()
        
        return jsonify({'message': '删除成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/stats/reorder', methods=['POST'])
def reorder_stats():
    """重新排序项目统计"""
    try:
        data = request.json
        stats_ids = data.get('stats_ids', [])
        
        with get_db() as conn:
            for index, stats_id in enumerate(stats_ids):
                conn.execute(
                    "UPDATE innovation_stats SET sort_order = ?, updated_at = ? WHERE id = ?",
                    (index, datetime.now(), stats_id)
                )
            conn.commit()
        
        return jsonify({'message': '排序保存成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ 前端数据接口 ============

@innovation_bp.route('/frontend/stats', methods=['GET'])
def get_frontend_stats():
    """获取前端显示的项目统计"""
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM innovation_stats WHERE status = 'active' ORDER BY sort_order ASC")
            stats = cursor.fetchall()
            
            result = []
            for stat in stats:
                stat_dict = dict(stat)
                result.append(stat_dict)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/frontend/achievements', methods=['GET'])
def get_frontend_achievements():
    """获取前端显示的成果与荣誉"""
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM achievements WHERE status = 'active' ORDER BY sort_order ASC")
            achievements = cursor.fetchall()
            
            # 按类型分组
            result = {
                'awards': [],
                'patents': []
            }
            
            for achievement in achievements:
                achievement_dict = dict(achievement)
                if achievement_dict['type'] == 'award':
                    result['awards'].append(achievement_dict)
                elif achievement_dict['type'] == 'patent':
                    result['patents'].append(achievement_dict)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/frontend/carousel', methods=['GET'])
def get_frontend_carousel():
    """获取前端显示的轮播图"""
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM innovation_carousel WHERE status = 'active' ORDER BY sort_order ASC")
            carousels = cursor.fetchall()
            
            result = []
            for carousel in carousels:
                carousel_dict = dict(carousel)
                carousel_dict['image_display_url'] = carousel_dict.get('image_url', '')
                result.append(carousel_dict)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/frontend/training-projects', methods=['GET'])
def get_frontend_training_projects():
    """获取前端显示的大学生创新创业训练计划"""
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM innovation_training_projects WHERE status = 'active' ORDER BY sort_order ASC")
            projects = cursor.fetchall()
            
            result = []
            for project in projects:
                project_dict = dict(project)
                project_dict['image_display_url'] = project_dict.get('image_url', '')
                result.append(project_dict)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/frontend/intellectual-properties', methods=['GET'])
def get_frontend_intellectual_properties():
    """获取前端显示的知识产权"""
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM intellectual_properties WHERE status = 'active' ORDER BY sort_order ASC")
            properties = cursor.fetchall()
            
            result = []
            for property in properties:
                property_dict = dict(property)
                property_dict['image_display_url'] = property_dict.get('image_url', '')
                result.append(property_dict)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/frontend/enterprise-cooperations', methods=['GET'])
def get_frontend_enterprise_cooperations():
    """获取前端显示的校企合作"""
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM enterprise_cooperations WHERE status = 'active' ORDER BY sort_order ASC")
            cooperations = cursor.fetchall()
            
            result = []
            for cooperation in cooperations:
                cooperation_dict = dict(cooperation)
                cooperation_dict['image_display_url'] = cooperation_dict.get('image_url', '')
                result.append(cooperation_dict)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500 

# ============ 管理后台API端点 ============

# ============ 轮播图管理 ============

@innovation_bp.route('/carousel', methods=['GET'])
def get_carousel():
    """获取轮播图列表"""
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM innovation_carousel ORDER BY sort_order ASC")
            carousels = cursor.fetchall()
            
            result = []
            for carousel in carousels:
                carousel_dict = dict(carousel)
                carousel_dict['image_display_url'] = carousel_dict.get('image_url', '')
                result.append(carousel_dict)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/carousel', methods=['POST'])
def create_carousel():
    """创建轮播图"""
    try:
        data = request.json
        
        with get_db() as conn:
            # 获取最大排序值
            cursor = conn.execute('SELECT COALESCE(MAX(sort_order), 0) FROM innovation_carousel')
            max_sort = cursor.fetchone()[0]
            
            # 插入新记录
            cursor = conn.execute(
                "INSERT INTO innovation_carousel (title, description, image_url, link_url, text_position, overlay_opacity, status, sort_order, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    data.get('title'),
                    data.get('description'),
                    data.get('image_url'),
                    data.get('link_url'),
                    data.get('text_position', 'bottom-left'),
                    data.get('overlay_opacity', 0.3),
                    data.get('status', 'active'),
                    max_sort + 1,
                    datetime.now(),
                    datetime.now()
                )
            )
            conn.commit()
            
            # 获取新创建的记录
            cursor = conn.execute("SELECT * FROM innovation_carousel WHERE id = ?", (cursor.lastrowid,))
            new_carousel = cursor.fetchone()
            
            if new_carousel:
                return jsonify(dict(new_carousel)), 201
            else:
                return jsonify({'error': '创建失败'}), 500
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/carousel/<int:carousel_id>', methods=['PUT'])
def update_carousel(carousel_id):
    """更新轮播图"""
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM innovation_carousel WHERE id = ?", (carousel_id,))
            carousel = cursor.fetchone()
            if not carousel:
                abort(404)
            
            data = request.json
            
            # 更新记录
            conn.execute(
                "UPDATE innovation_carousel SET title = ?, description = ?, image_url = ?, link_url = ?, text_position = ?, overlay_opacity = ?, status = ?, updated_at = ? WHERE id = ?",
                (
                    data.get('title', carousel['title']),
                    data.get('description', carousel['description']),
                    data.get('image_url', carousel['image_url']),
                    data.get('link_url', carousel['link_url']),
                    data.get('text_position', carousel['text_position']),
                    data.get('overlay_opacity', carousel['overlay_opacity']),
                    data.get('status', carousel['status']),
                    datetime.now(),
                    carousel_id
                )
            )
            conn.commit()
            
            # 获取更新后的记录
            cursor = conn.execute("SELECT * FROM innovation_carousel WHERE id = ?", (carousel_id,))
            updated_carousel = cursor.fetchone()
            
            return jsonify(dict(updated_carousel))
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/carousel/<int:carousel_id>', methods=['DELETE'])
def delete_carousel(carousel_id):
    """删除轮播图"""
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM innovation_carousel WHERE id = ?", (carousel_id,))
            carousel = cursor.fetchone()
            if not carousel:
                abort(404)
            
            conn.execute("DELETE FROM innovation_carousel WHERE id = ?", (carousel_id,))
            conn.commit()
        
        return jsonify({'message': '删除成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/carousel/reorder', methods=['POST'])
def reorder_carousel():
    """重新排序轮播图"""
    try:
        data = request.json
        carousel_ids = data.get('carousel_ids', [])
        
        with get_db() as conn:
            for index, carousel_id in enumerate(carousel_ids):
                conn.execute(
                    "UPDATE innovation_carousel SET sort_order = ?, updated_at = ? WHERE id = ?",
                    (index, datetime.now(), carousel_id)
                )
            conn.commit()
        
        return jsonify({'message': '排序保存成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/carousel/upload', methods=['POST'])
def upload_carousel_image():
    """上传轮播图图片"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '未找到上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '文件名为空'}), 400
        
        # 检查文件类型
        if not allowed_file(file.filename):
            return jsonify({'error': '不支持的文件类型'}), 400
        
        # 保存文件
        filename = ensure_upload_dir('carousel', file)
        
        return jsonify({
            'success': True,
            'url': f'/static/uploads/carousel/{filename}',
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ 成果与荣誉管理 ============

@innovation_bp.route('/achievements', methods=['GET'])
def get_achievements():
    """获取成果与荣誉列表"""
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM achievements ORDER BY sort_order ASC")
            achievements = cursor.fetchall()
            
            result = []
            for achievement in achievements:
                achievement_dict = dict(achievement)
                result.append(achievement_dict)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/achievements', methods=['POST'])
def create_achievement():
    """创建成果与荣誉"""
    try:
        data = request.json
        
        with get_db() as conn:
            # 获取最大排序值
            cursor = conn.execute('SELECT COALESCE(MAX(sort_order), 0) FROM achievements')
            max_sort = cursor.fetchone()[0]
            
            # 插入新记录
            cursor = conn.execute(
                "INSERT INTO achievements (title, type, description, date, icon, status, extra_data, sort_order, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    data.get('title'),
                    data.get('type', 'award'),
                    data.get('description'),
                    data.get('date'),
                    data.get('icon'),
                    data.get('status', 'active'),
                    json.dumps(data.get('extra_data')) if data.get('extra_data') else None,
                    max_sort + 1,
                    datetime.now(),
                    datetime.now()
                )
            )
            conn.commit()
            
            # 获取新创建的记录
            cursor = conn.execute("SELECT * FROM achievements WHERE id = ?", (cursor.lastrowid,))
            new_achievement = cursor.fetchone()
            
            if new_achievement:
                return jsonify(dict(new_achievement)), 201
            else:
                return jsonify({'error': '创建失败'}), 500
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/achievements/<int:achievement_id>', methods=['PUT'])
def update_achievement(achievement_id):
    """更新成果与荣誉"""
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM achievements WHERE id = ?", (achievement_id,))
            achievement = cursor.fetchone()
            if not achievement:
                abort(404)
            
            data = request.json
            
            # 更新记录
            conn.execute(
                "UPDATE achievements SET title = ?, type = ?, description = ?, date = ?, icon = ?, status = ?, extra_data = ?, updated_at = ? WHERE id = ?",
                (
                    data.get('title', achievement['title']),
                    data.get('type', achievement['type']),
                    data.get('description', achievement['description']),
                    data.get('date', achievement['date']),
                    data.get('icon', achievement['icon']),
                    data.get('status', achievement['status']),
                    json.dumps(data.get('extra_data')) if data.get('extra_data') else None,
                    datetime.now(),
                    achievement_id
                )
            )
            conn.commit()
            
            # 获取更新后的记录
            cursor = conn.execute("SELECT * FROM achievements WHERE id = ?", (achievement_id,))
            updated_achievement = cursor.fetchone()
            
            return jsonify(dict(updated_achievement))
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/achievements/<int:achievement_id>', methods=['DELETE'])
def delete_achievement(achievement_id):
    """删除成果与荣誉"""
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM achievements WHERE id = ?", (achievement_id,))
            achievement = cursor.fetchone()
            if not achievement:
                abort(404)
            
            conn.execute("DELETE FROM achievements WHERE id = ?", (achievement_id,))
            conn.commit()
        
        return jsonify({'message': '删除成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/achievements/reorder', methods=['POST'])
def reorder_achievements():
    """重新排序成果与荣誉"""
    try:
        data = request.json
        achievement_ids = data.get('achievement_ids', [])
        
        with get_db() as conn:
            for index, achievement_id in enumerate(achievement_ids):
                conn.execute(
                    "UPDATE achievements SET sort_order = ?, updated_at = ? WHERE id = ?",
                    (index, datetime.now(), achievement_id)
                )
            conn.commit()
        
        return jsonify({'message': '排序保存成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ 大学生创新创业训练计划管理 ============

@innovation_bp.route('/training-projects', methods=['GET'])
def get_training_projects():
    """获取训练计划列表"""
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM innovation_training_projects ORDER BY sort_order ASC")
            projects = cursor.fetchall()
            
            result = []
            for project in projects:
                project_dict = dict(project)
                project_dict['image_display_url'] = project_dict.get('image_url', '')
                result.append(project_dict)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/training-projects', methods=['POST'])
def create_training_project():
    """创建训练计划"""
    try:
        data = request.json
        
        with get_db() as conn:
            # 获取最大排序值
            cursor = conn.execute('SELECT COALESCE(MAX(sort_order), 0) FROM innovation_training_projects')
            max_sort = cursor.fetchone()[0]
            
            # 插入新记录
            cursor = conn.execute(
                "INSERT INTO innovation_training_projects (title, description, category, progress, start_date, end_date, budget, leader, members_count, contact_email, contact_phone, contact_wechat, image_url, status, sort_order, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    data.get('title'),
                    data.get('description'),
                    data.get('category', '人工智能'),
                    data.get('progress', 0),
                    data.get('start_date'),
                    data.get('end_date'),
                    data.get('budget'),
                    data.get('leader'),
                    data.get('members_count', 0),
                    data.get('contact_email'),
                    data.get('contact_phone'),
                    data.get('contact_wechat'),
                    data.get('image_url'),
                    data.get('status', 'active'),
                    max_sort + 1,
                    datetime.now(),
                    datetime.now()
                )
            )
            conn.commit()
            
            # 获取新创建的记录
            cursor = conn.execute("SELECT * FROM innovation_training_projects WHERE id = ?", (cursor.lastrowid,))
            new_project = cursor.fetchone()
            
            if new_project:
                return jsonify(dict(new_project)), 201
            else:
                return jsonify({'error': '创建失败'}), 500
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/training-projects/<int:project_id>', methods=['PUT'])
def update_training_project(project_id):
    """更新训练计划"""
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM innovation_training_projects WHERE id = ?", (project_id,))
            project = cursor.fetchone()
            if not project:
                abort(404)
            
            data = request.json
            
            # 更新记录
            conn.execute(
                "UPDATE innovation_training_projects SET title = ?, description = ?, category = ?, progress = ?, start_date = ?, end_date = ?, budget = ?, leader = ?, members_count = ?, contact_email = ?, contact_phone = ?, contact_wechat = ?, image_url = ?, status = ?, updated_at = ? WHERE id = ?",
                (
                    data.get('title', project['title']),
                    data.get('description', project['description']),
                    data.get('category', project['category']),
                    data.get('progress', project['progress']),
                    data.get('start_date', project['start_date']),
                    data.get('end_date', project['end_date']),
                    data.get('budget', project['budget']),
                    data.get('leader', project['leader']),
                    data.get('members_count', project['members_count']),
                    data.get('contact_email', project['contact_email']),
                    data.get('contact_phone', project['contact_phone']),
                    data.get('contact_wechat', project['contact_wechat']),
                    data.get('image_url', project['image_url']),
                    data.get('status', project['status']),
                    datetime.now(),
                    project_id
                )
            )
            conn.commit()
            
            # 获取更新后的记录
            cursor = conn.execute("SELECT * FROM innovation_training_projects WHERE id = ?", (project_id,))
            updated_project = cursor.fetchone()
            
            return jsonify(dict(updated_project))
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/training-projects/<int:project_id>', methods=['DELETE'])
def delete_training_project(project_id):
    """删除训练计划"""
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM innovation_training_projects WHERE id = ?", (project_id,))
            project = cursor.fetchone()
            if not project:
                abort(404)
            
            conn.execute("DELETE FROM innovation_training_projects WHERE id = ?", (project_id,))
            conn.commit()
        
        return jsonify({'message': '删除成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/training-projects/reorder', methods=['POST'])
def reorder_training_projects():
    """重新排序训练计划"""
    try:
        data = request.json
        project_ids = data.get('project_ids', [])
        
        with get_db() as conn:
            for index, project_id in enumerate(project_ids):
                conn.execute(
                    "UPDATE innovation_training_projects SET sort_order = ?, updated_at = ? WHERE id = ?",
                    (index, datetime.now(), project_id)
                )
            conn.commit()
        
        return jsonify({'message': '排序保存成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/training-projects/upload', methods=['POST'])
def upload_training_project_image():
    """上传训练计划图片"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '未找到上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '文件名为空'}), 400
        
        # 检查文件类型
        if not allowed_file(file.filename):
            return jsonify({'error': '不支持的文件类型'}), 400
        
        # 保存文件
        filename = ensure_upload_dir('training_projects', file)
        
        return jsonify({
            'success': True,
            'url': f'/static/uploads/training_projects/{filename}',
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ 知识产权管理 ============

@innovation_bp.route('/intellectual-properties', methods=['GET'])
def get_intellectual_properties():
    """获取知识产权列表"""
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM intellectual_properties ORDER BY sort_order ASC")
            properties = cursor.fetchall()
            
            result = []
            for property in properties:
                property_dict = dict(property)
                property_dict['image_display_url'] = property_dict.get('image_url', '')
                result.append(property_dict)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/intellectual-properties', methods=['POST'])
def create_intellectual_property():
    """创建知识产权"""
    try:
        data = request.json
        
        with get_db() as conn:
            # 获取最大排序值
            cursor = conn.execute('SELECT COALESCE(MAX(sort_order), 0) FROM intellectual_properties')
            max_sort = cursor.fetchone()[0]
            
            # 插入新记录
            cursor = conn.execute(
                "INSERT INTO intellectual_properties (title, description, type, category, application_date, grant_date, patent_number, inventors, image_url, status, sort_order, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    data.get('title'),
                    data.get('description'),
                    data.get('type', 'patent'),
                    data.get('category'),
                    data.get('application_date'),
                    data.get('grant_date'),
                    data.get('patent_number'),
                    data.get('inventors'),
                    data.get('image_url'),
                    data.get('status', 'active'),
                    max_sort + 1,
                    datetime.now(),
                    datetime.now()
                )
            )
            conn.commit()
            
            # 获取新创建的记录
            cursor = conn.execute("SELECT * FROM intellectual_properties WHERE id = ?", (cursor.lastrowid,))
            new_property = cursor.fetchone()
            
            if new_property:
                return jsonify(dict(new_property)), 201
            else:
                return jsonify({'error': '创建失败'}), 500
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/intellectual-properties/<int:property_id>', methods=['PUT'])
def update_intellectual_property(property_id):
    """更新知识产权"""
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM intellectual_properties WHERE id = ?", (property_id,))
            property = cursor.fetchone()
            if not property:
                abort(404)
            
            data = request.json
            
            # 更新记录
            conn.execute(
                "UPDATE intellectual_properties SET title = ?, description = ?, type = ?, category = ?, application_date = ?, grant_date = ?, patent_number = ?, inventors = ?, image_url = ?, status = ?, updated_at = ? WHERE id = ?",
                (
                    data.get('title', property['title']),
                    data.get('description', property['description']),
                    data.get('type', property['type']),
                    data.get('category', property['category']),
                    data.get('application_date', property['application_date']),
                    data.get('grant_date', property['grant_date']),
                    data.get('patent_number', property['patent_number']),
                    data.get('inventors', property['inventors']),
                    data.get('image_url', property['image_url']),
                    data.get('status', property['status']),
                    datetime.now(),
                    property_id
                )
            )
            conn.commit()
            
            # 获取更新后的记录
            cursor = conn.execute("SELECT * FROM intellectual_properties WHERE id = ?", (property_id,))
            updated_property = cursor.fetchone()
            
            return jsonify(dict(updated_property))
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/intellectual-properties/<int:property_id>', methods=['DELETE'])
def delete_intellectual_property(property_id):
    """删除知识产权"""
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM intellectual_properties WHERE id = ?", (property_id,))
            property = cursor.fetchone()
            if not property:
                abort(404)
            
            conn.execute("DELETE FROM intellectual_properties WHERE id = ?", (property_id,))
            conn.commit()
        
        return jsonify({'message': '删除成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/intellectual-properties/reorder', methods=['POST'])
def reorder_intellectual_properties():
    """重新排序知识产权"""
    try:
        data = request.json
        property_ids = data.get('property_ids', [])
        
        with get_db() as conn:
            for index, property_id in enumerate(property_ids):
                conn.execute(
                    "UPDATE intellectual_properties SET sort_order = ?, updated_at = ? WHERE id = ?",
                    (index, datetime.now(), property_id)
                )
            conn.commit()
        
        return jsonify({'message': '排序保存成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/intellectual-properties/upload', methods=['POST'])
def upload_intellectual_property_image():
    """上传知识产权图片"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '未找到上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '文件名为空'}), 400
        
        # 检查文件类型
        if not allowed_file(file.filename):
            return jsonify({'error': '不支持的文件类型'}), 400
        
        # 保存文件
        filename = ensure_upload_dir('intellectual_properties', file)
        
        return jsonify({
            'success': True,
            'url': f'/static/uploads/intellectual_properties/{filename}',
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ 校企合作管理 ============

@innovation_bp.route('/enterprise-cooperations', methods=['GET'])
def get_enterprise_cooperations():
    """获取校企合作列表"""
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM enterprise_cooperations ORDER BY sort_order ASC")
            cooperations = cursor.fetchall()
            
            result = []
            for cooperation in cooperations:
                cooperation_dict = dict(cooperation)
                cooperation_dict['image_display_url'] = cooperation_dict.get('image_url', '')
                result.append(cooperation_dict)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/enterprise-cooperations', methods=['POST'])
def create_enterprise_cooperation():
    """创建校企合作"""
    try:
        data = request.json
        
        with get_db() as conn:
            # 获取最大排序值
            cursor = conn.execute('SELECT COALESCE(MAX(sort_order), 0) FROM enterprise_cooperations')
            max_sort = cursor.fetchone()[0]
            
            # 插入新记录
            cursor = conn.execute(
                "INSERT INTO enterprise_cooperations (title, description, enterprise_name, category, start_date, end_date, budget, leader, achievement, enterprise_logo, image_url, status, sort_order, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    data.get('title'),
                    data.get('description'),
                    data.get('enterprise_name'),
                    data.get('category'),
                    data.get('start_date'),
                    data.get('end_date'),
                    data.get('budget'),
                    data.get('leader'),
                    data.get('achievement'),
                    data.get('enterprise_logo'),
                    data.get('image_url'),
                    data.get('status', 'active'),
                    max_sort + 1,
                    datetime.now(),
                    datetime.now()
                )
            )
            conn.commit()
            
            # 获取新创建的记录
            cursor = conn.execute("SELECT * FROM enterprise_cooperations WHERE id = ?", (cursor.lastrowid,))
            new_cooperation = cursor.fetchone()
            
            if new_cooperation:
                return jsonify(dict(new_cooperation)), 201
            else:
                return jsonify({'error': '创建失败'}), 500
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/enterprise-cooperations/<int:cooperation_id>', methods=['PUT'])
def update_enterprise_cooperation(cooperation_id):
    """更新校企合作"""
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM enterprise_cooperations WHERE id = ?", (cooperation_id,))
            cooperation = cursor.fetchone()
            if not cooperation:
                abort(404)
            
            data = request.json
            
            # 更新记录
            conn.execute(
                "UPDATE enterprise_cooperations SET title = ?, description = ?, enterprise_name = ?, category = ?, start_date = ?, end_date = ?, budget = ?, leader = ?, achievement = ?, enterprise_logo = ?, image_url = ?, status = ?, updated_at = ? WHERE id = ?",
                (
                    data.get('title', cooperation['title']),
                    data.get('description', cooperation['description']),
                    data.get('enterprise_name', cooperation['enterprise_name']),
                    data.get('category', cooperation['category']),
                    data.get('start_date', cooperation['start_date']),
                    data.get('end_date', cooperation['end_date']),
                    data.get('budget', cooperation['budget']),
                    data.get('leader', cooperation['leader']),
                    data.get('achievement', cooperation['achievement']),
                    data.get('enterprise_logo', cooperation['enterprise_logo']),
                    data.get('image_url', cooperation['image_url']),
                    data.get('status', cooperation['status']),
                    datetime.now(),
                    cooperation_id
                )
            )
            conn.commit()
            
            # 获取更新后的记录
            cursor = conn.execute("SELECT * FROM enterprise_cooperations WHERE id = ?", (cooperation_id,))
            updated_cooperation = cursor.fetchone()
            
            return jsonify(dict(updated_cooperation))
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/enterprise-cooperations/<int:cooperation_id>', methods=['DELETE'])
def delete_enterprise_cooperation(cooperation_id):
    """删除校企合作"""
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM enterprise_cooperations WHERE id = ?", (cooperation_id,))
            cooperation = cursor.fetchone()
            if not cooperation:
                abort(404)
            
            conn.execute("DELETE FROM enterprise_cooperations WHERE id = ?", (cooperation_id,))
            conn.commit()
        
        return jsonify({'message': '删除成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/enterprise-cooperations/reorder', methods=['POST'])
def reorder_enterprise_cooperations():
    """重新排序校企合作"""
    try:
        data = request.json
        cooperation_ids = data.get('cooperation_ids', [])
        
        with get_db() as conn:
            for index, cooperation_id in enumerate(cooperation_ids):
                conn.execute(
                    "UPDATE enterprise_cooperations SET sort_order = ?, updated_at = ? WHERE id = ?",
                    (index, datetime.now(), cooperation_id)
                )
            conn.commit()
        
        return jsonify({'message': '排序保存成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@innovation_bp.route('/enterprise-cooperations/upload', methods=['POST'])
def upload_enterprise_cooperation_image():
    """上传校企合作图片"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '未找到上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '文件名为空'}), 400
        
        # 检查文件类型
        if not allowed_file(file.filename):
            return jsonify({'error': '不支持的文件类型'}), 400
        
        # 保存文件
        filename = ensure_upload_dir('enterprise_cooperations', file)
        
        return jsonify({
            'success': True,
            'url': f'/static/uploads/enterprise_cooperations/{filename}',
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 