#!/usr/bin/env python3
"""
团队成员管理API - 重写版本
使用原生sqlite3，移除SQLAlchemy依赖
"""

from flask import Blueprint, request, jsonify, abort, session
from db_utils import get_db
# from socket_utils import notify_page_refresh
import logging
import json
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

team_bp = Blueprint('team', __name__)

@team_bp.route('/api/team', methods=['GET'])
def get_team_members():
    """获取所有团队成员，按年级分组"""
    try:
        with get_db() as conn:
            # 修改排序逻辑：优先按order_index排序，然后按年级和创建时间
            cursor = conn.execute('''
                SELECT * FROM team_members 
                ORDER BY COALESCE(order_index, 999999) ASC, grade DESC, created_at DESC
            ''')
            all_members = cursor.fetchall()
            
            # 按年级分组
            grade_groups = {}
            for member in all_members:
                member_dict = dict(member)
                grade = member_dict.get('grade') or '2024级'
                
                if grade not in grade_groups:
                    grade_groups[grade] = []
                
                grade_groups[grade].append({
                    'id': member_dict['id'],
                    'name': member_dict['name'] or '',
                    'position': member_dict['position'] or '',
                    'role': member_dict['position'] or '',
                    'desc': member_dict['description'] or '',
                    'description': member_dict['description'] or '',
                    'img': member_dict['image_url'] or '',
                    'image_url': member_dict['image_url'] or '',
                    'qq': member_dict['qq'] or '',
                    'wechat': member_dict['wechat'] or '',
                    'email': member_dict['email'] or '',
                    'grade': grade,
                    'order_index': member_dict['order_index'] if member_dict['order_index'] is not None else 0,
                    'created_at': member_dict['created_at'],
                    'updated_at': member_dict['updated_at']
                })
            
            # 转换为前端期望的格式
            grade_data = []
            for grade, members in grade_groups.items():
                # 确保每个年级内的成员也按order_index排序
                members.sort(key=lambda x: x.get('order_index', 0))
                grade_data.append({
                    'grade': grade,
                    'members': members
                })
            
            # 按年级名称降序排序
            grade_data.sort(key=lambda x: x['grade'], reverse=True)
            
            logger.info(f"获取团队成员成功，共{len(grade_data)}个年级，{len(all_members)}个成员")
            return jsonify(grade_data), 200
    except Exception as e:
        logger.error(f"获取团队成员失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': '获取团队成员失败'}), 500

@team_bp.route('/api/team', methods=['POST'])
def create_team_member():
    """创建新团队成员"""
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
        qq = str(data.get('qq', '')).strip()
        wechat = str(data.get('wechat', '')).strip()
        email = str(data.get('email', '')).strip()
        grade = str(data.get('grade', '2024级')).strip()
        
        # 如果没有position但有role，使用role作为position
        if not position and data.get('role'):
            position = str(data.get('role', '')).strip()
        
        # 如果没有image_url但有img，使用img作为image_url
        if not image_url and data.get('img'):
            image_url = str(data.get('img', '')).strip()
        
        # 验证必填字段
        if not name:
            return jsonify({"error": "姓名不能为空"}), 400
        
        with get_db() as conn:
            # 获取最大排序索引
            cursor = conn.execute('SELECT COALESCE(MAX(order_index), 0) FROM team_members')
            max_order = cursor.fetchone()[0]
            
            # 插入新成员
            cursor = conn.execute('''
                INSERT INTO team_members (name, position, description, image_url, qq, wechat, email, grade, order_index, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                name, position, description, image_url, qq, wechat, email, grade,
                max_order + 1, datetime.now().isoformat(), datetime.now().isoformat()
            ))
            
            member_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"创建团队成员成功: {name}")
            
            # 通知前端刷新
            try:
                from socket_utils import notify_page_refresh
                notify_page_refresh('team', {'action': 'created', 'member_id': member_id})
                notify_page_refresh('home', {'action': 'created', 'member_id': member_id})
            except Exception as e:
                logger.warning(f"通知前端刷新失败: {e}")
                # 不影响主要功能
            
            return jsonify({
                "success": True,
                "message": "团队成员创建成功",
                "member_id": member_id
            }), 201
            
    except Exception as e:
        logger.error(f"创建团队成员失败: {e}")
        return jsonify({"error": f"创建失败: {str(e)}"}), 500

@team_bp.route('/api/team/<int:member_id>', methods=['PUT'])
def update_team_member(member_id):
    """更新团队成员信息"""
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({"error": "未授权"}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据为空"}), 400
        
        with get_db() as conn:
            # 检查成员是否存在
            cursor = conn.execute('SELECT * FROM team_members WHERE id = ?', (member_id,))
            if not cursor.fetchone():
                return jsonify({"error": "团队成员不存在"}), 404
            
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
            
            if 'description' in data or 'desc' in data:
                desc = data.get('description') or data.get('desc', '')
                update_fields.append('description = ?')
                update_values.append(str(desc).strip())
            
            if 'image_url' in data or 'img' in data:
                img = data.get('image_url') or data.get('img', '')
                update_fields.append('image_url = ?')
                update_values.append(str(img).strip())
            
            if 'qq' in data:
                update_fields.append('qq = ?')
                update_values.append(str(data['qq']).strip())
            
            if 'wechat' in data:
                update_fields.append('wechat = ?')
                update_values.append(str(data['wechat']).strip())
            
            if 'email' in data:
                update_fields.append('email = ?')
                update_values.append(str(data['email']).strip())
            
            if 'grade' in data:
                update_fields.append('grade = ?')
                update_values.append(str(data['grade']).strip())
            
            # 添加更新时间
            update_fields.append('updated_at = ?')
            update_values.append(datetime.now().isoformat())
            
            # 添加成员ID到值列表
            update_values.append(member_id)
            
            # 执行更新
            if update_fields:
                sql = f'UPDATE team_members SET {", ".join(update_fields)} WHERE id = ?'
                conn.execute(sql, update_values)
                conn.commit()
                
                logger.info(f"更新团队成员成功: ID={member_id}")
                
                # 通知前端刷新
                try:
                    from socket_utils import notify_page_refresh
                    notify_page_refresh('team', {'action': 'updated', 'member_id': member_id})
                    notify_page_refresh('home', {'action': 'updated', 'member_id': member_id})
                except Exception as e:
                    logger.warning(f"通知前端刷新失败: {e}")
                
                return jsonify({"success": True, "message": "更新成功"})
            else:
                return jsonify({"error": "没有需要更新的字段"}), 400
                
    except Exception as e:
        logger.error(f"更新团队成员失败: {e}")
        return jsonify({"error": f"更新失败: {str(e)}"}), 500

@team_bp.route('/api/team/<int:member_id>', methods=['DELETE'])
def delete_team_member(member_id):
    """删除团队成员"""
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({"error": "未授权"}), 401
    
    try:
        with get_db() as conn:
            # 检查成员是否存在
            cursor = conn.execute('SELECT * FROM team_members WHERE id = ?', (member_id,))
            member = cursor.fetchone()
            if not member:
                return jsonify({"error": "团队成员不存在"}), 404
            
            # 删除成员
            conn.execute('DELETE FROM team_members WHERE id = ?', (member_id,))
            conn.commit()
            
            logger.info(f"删除团队成员成功: {member['name']}")
            
            # 通知前端刷新
            try:
                from socket_utils import notify_page_refresh
                notify_page_refresh('team', {'action': 'deleted', 'member_id': member_id})
                notify_page_refresh('home', {'action': 'deleted', 'member_id': member_id})
            except Exception as e:
                logger.warning(f"通知前端刷新失败: {e}")
            
            return jsonify({"success": True, "message": "删除成功"})
            
    except Exception as e:
        logger.error(f"删除团队成员失败: {e}")
        return jsonify({"error": f"删除失败: {str(e)}"}), 500

@team_bp.route('/api/test-notification', methods=['POST'])
def test_notification():
    """测试通知功能"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据为空"}), 400
        
        page = data.get('page', 'home')
        notification_type = data.get('type', 'test')
        operation = data.get('operation', 'test')
        payload = data.get('payload', {})
        
        logger.info(f"收到测试通知请求: {page}, {notification_type}, {operation}")
        
        # 尝试发送Socket.IO通知
        try:
            from socket_utils import notify_page_refresh
            notify_page_refresh(page, {
                'type': notification_type,
                'operation': operation,
                'payload': payload,
                'test': True
            })
            logger.info(f"测试通知已发送到 {page}")
        except Exception as e:
            logger.warning(f"发送测试通知失败: {e}")
        
        return jsonify({
            "success": True,
            "message": "测试通知已发送",
            "page": page,
            "type": notification_type,
            "operation": operation
        })
        
    except Exception as e:
        logger.error(f"处理测试通知失败: {e}")
        return jsonify({"error": f"处理失败: {str(e)}"}), 500

@team_bp.route('/api/team/reorder', methods=['POST'])
def reorder_team_members():
    """重新排序团队成员"""
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({"error": "未授权"}), 401
    
    try:
        data = request.get_json()
        if not data or 'member_ids' not in data:
            return jsonify({"error": "缺少排序数据"}), 400
        
        member_ids = data['member_ids']
        if not isinstance(member_ids, list):
            return jsonify({"error": "排序数据格式错误"}), 400
        
        logger.info(f"开始更新团队成员排序，成员ID列表: {member_ids}")
        
        with get_db() as conn:
            # 验证所有成员ID是否存在
            placeholders = ','.join(['?' for _ in member_ids])
            cursor = conn.execute(f'SELECT id FROM team_members WHERE id IN ({placeholders})', member_ids)
            existing_ids = [row[0] for row in cursor.fetchall()]
            
            if len(existing_ids) != len(member_ids):
                missing_ids = set(member_ids) - set(existing_ids)
                logger.warning(f"部分成员ID不存在: {missing_ids}")
                return jsonify({"error": f"部分成员ID不存在: {missing_ids}"}), 400
            
            # 批量更新排序
            for index, member_id in enumerate(member_ids):
                new_order = index + 1
                conn.execute('UPDATE team_members SET order_index = ?, updated_at = ? WHERE id = ?', 
                           (new_order, datetime.now().isoformat(), member_id))
                logger.debug(f"更新成员ID {member_id} 的排序为 {new_order}")
            
            conn.commit()
            
            logger.info(f"团队成员排序更新成功，共{len(member_ids)}个成员")
            
            # 通知前端刷新
            try:
                from socket_utils import notify_page_refresh
                notify_page_refresh('team', {'action': 'reordered', 'member_ids': member_ids})
                notify_page_refresh('home', {'action': 'reordered', 'member_ids': member_ids})
            except Exception as e:
                logger.warning(f"通知前端刷新失败: {e}")
            
            return jsonify({"success": True, "message": "排序更新成功"})
            
    except Exception as e:
        logger.error(f"更新团队成员排序失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"排序更新失败: {str(e)}"}), 500

# 研究领域管理API
@team_bp.route('/api/research-areas', methods=['GET'])
def get_research_areas():
    """获取所有研究领域"""
    try:
        with get_db() as conn:
            cursor = conn.execute('''
                SELECT * FROM research_areas 
                ORDER BY order_index ASC, created_at DESC
            ''')
            areas = []
            for row in cursor.fetchall():
                area_dict = dict(row)
                # 添加前端期望的字段别名
                area_dict['title'] = area_dict.get('title', '')
                area_dict['desc'] = area_dict.get('description', '')
                areas.append(area_dict)
            
            return jsonify(areas)
    except Exception as e:
        logger.error(f"获取研究领域失败: {e}")
        return jsonify({'error': '获取研究领域失败'}), 500

@team_bp.route('/api/research-areas', methods=['POST'])
def create_research_area():
    """创建新研究领域"""
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({"error": "未授权"}), 401
    
    try:
        data = request.get_json()
        if not data or not data.get('title'):
            return jsonify({"error": "研究领域标题不能为空"}), 400
        
        title = str(data['title']).strip()
        category = str(data.get('category', '深度学习')).strip()
        description = str(data.get('description', '')).strip()
        members = data.get('members', [])
        
        # 如果members是列表，转换为JSON字符串
        if isinstance(members, list):
            members = json.dumps(members, ensure_ascii=False)
        else:
            members = str(members)
        
        with get_db() as conn:
            # 获取最大排序索引
            cursor = conn.execute('SELECT COALESCE(MAX(order_index), 0) FROM research_areas')
            max_order = cursor.fetchone()[0]
            
            # 插入新研究领域
            cursor = conn.execute('''
                INSERT INTO research_areas (title, category, description, members, order_index, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, category, description, members, max_order + 1, datetime.now().isoformat(), datetime.now().isoformat()))
            
            area_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"创建研究领域成功: {title}")
            
            # 通知前端刷新
            # notify_page_refresh('research_areas', {'action': 'created', 'area_id': area_id})
            
            return jsonify({
                "success": True,
                "message": "研究领域创建成功",
                "area_id": area_id
            }), 201
            
    except Exception as e:
        logger.error(f"创建研究领域失败: {e}")
        return jsonify({"error": f"创建失败: {str(e)}"}), 500

@team_bp.route('/api/research-areas/<int:area_id>', methods=['PUT'])
def update_research_area(area_id):
    """更新研究领域"""
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({"error": "未授权"}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据为空"}), 400
        
        with get_db() as conn:
            # 检查研究领域是否存在
            cursor = conn.execute('SELECT * FROM research_areas WHERE id = ?', (area_id,))
            if not cursor.fetchone():
                return jsonify({"error": "研究领域不存在"}), 404
            
            # 构建更新字段
            update_fields = []
            update_values = []
            
            if 'title' in data:
                update_fields.append('title = ?')
                update_values.append(str(data['title']).strip())
            
            if 'category' in data:
                update_fields.append('category = ?')
                update_values.append(str(data['category']).strip())
            
            if 'description' in data or 'desc' in data:
                desc = data.get('description') or data.get('desc', '')
                update_fields.append('description = ?')
                update_values.append(str(desc).strip())
            
            if 'members' in data:
                members = data['members']
                # 如果members是列表，转换为JSON字符串
                if isinstance(members, list):
                    members = json.dumps(members, ensure_ascii=False)
                else:
                    members = str(members)
                update_fields.append('members = ?')
                update_values.append(members)
            
            # 添加更新时间
            update_fields.append('updated_at = ?')
            update_values.append(datetime.now().isoformat())
            
            # 添加研究领域ID到值列表
            update_values.append(area_id)
            
            # 执行更新
            if update_fields:
                sql = f'UPDATE research_areas SET {", ".join(update_fields)} WHERE id = ?'
                conn.execute(sql, update_values)
                conn.commit()
                
                logger.info(f"更新研究领域成功: ID={area_id}")
                
                            # 通知前端刷新
            # notify_page_refresh('research_areas', {'action': 'updated', 'area_id': area_id})
                
                return jsonify({"success": True, "message": "更新成功"})
            else:
                return jsonify({"error": "没有需要更新的字段"}), 400
                
    except Exception as e:
        logger.error(f"更新研究领域失败: {e}")
        return jsonify({"error": f"更新失败: {str(e)}"}), 500

@team_bp.route('/api/research-areas/<int:area_id>', methods=['DELETE'])
def delete_research_area(area_id):
    """删除研究领域"""
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({"error": "未授权"}), 401
    
    try:
        with get_db() as conn:
            # 检查研究领域是否存在
            cursor = conn.execute('SELECT * FROM research_areas WHERE id = ?', (area_id,))
            area = cursor.fetchone()
            if not area:
                return jsonify({"error": "研究领域不存在"}), 404
            
            # 删除研究领域
            conn.execute('DELETE FROM research_areas WHERE id = ?', (area_id,))
            conn.commit()
            
            logger.info(f"删除研究领域成功: {area['title']}")
            
            # 通知前端刷新
            # notify_page_refresh('research_areas', {'action': 'deleted', 'area_id': area_id})
            
            return jsonify({"success": True, "message": "删除成功"})
            
    except Exception as e:
        logger.error(f"删除研究领域失败: {e}")
        return jsonify({"error": f"删除失败: {str(e)}"}), 500

@team_bp.route('/api/research-areas/reorder', methods=['POST'])
def reorder_research_areas():
    """重新排序研究领域"""
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({"error": "未授权"}), 401
    
    try:
        data = request.get_json()
        if not data or 'area_ids' not in data:
            return jsonify({"error": "缺少排序数据"}), 400
        
        area_ids = data['area_ids']
        if not isinstance(area_ids, list):
            return jsonify({"error": "排序数据格式错误"}), 400
        
        with get_db() as conn:
            # 批量更新排序
            for index, area_id in enumerate(area_ids):
                conn.execute('UPDATE research_areas SET order_index = ? WHERE id = ?', (index + 1, area_id))
            
            conn.commit()
            
            logger.info(f"研究领域排序更新成功，共{len(area_ids)}个领域")
            
            # 通知前端刷新
            # notify_page_refresh('research_areas', {'action': 'reordered', 'area_ids': area_ids})
            
            return jsonify({"success": True, "message": "排序更新成功"})
            
    except Exception as e:
        logger.error(f"更新研究领域排序失败: {e}")
        return jsonify({"error": f"排序更新失败: {str(e)}"}), 500 