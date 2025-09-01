# 研究领域API - 提供研究领域的CRUD操作和实时同步

from flask import Blueprint, request, jsonify
from db_utils import get_db
import json
from datetime import datetime
from socket_utils import notify_page_refresh

research_bp = Blueprint('research', __name__)

@research_bp.route('/api/research', methods=['GET'])
def get_research_areas():
    """获取研究领域列表，支持分页和分类筛选"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 6))
        category = request.args.get('category', '')
        
        with get_db() as conn:
            # 构建查询条件
            where_clause = ""
            params = []
            
            if category and category != '全部':
                where_clause = "WHERE category = ?"
                params.append(category)
            
            # 获取总数
            count_sql = f"SELECT COUNT(*) FROM research_areas {where_clause}"
            cursor = conn.execute(count_sql, params)
            total = cursor.fetchone()[0]
            
            # 计算分页
            offset = (page - 1) * per_page
            total_pages = (total + per_page - 1) // per_page
            
            # 获取分页数据
            sql = f"""
                SELECT id, title, category, description, members, order_index, 
                       created_at, updated_at
                FROM research_areas 
                {where_clause}
                ORDER BY order_index ASC, created_at DESC
                LIMIT ? OFFSET ?
            """
            params.extend([per_page, offset])
            
            cursor = conn.execute(sql, params)
            areas = cursor.fetchall()
            
            # 格式化数据
            research_data = []
            for area in areas:
                # 解析成员信息
                members = []
                if area[4]:  # members字段
                    try:
                        members = json.loads(area[4]) if area[4] else []
                    except (json.JSONDecodeError, TypeError):
                        members = []
                
                research_data.append({
                    'id': area[0],
                    'title': area[1],
                    'category': area[2],
                    'description': area[3],
                    'members': members,
                    'order_index': area[5],
                    'created_at': area[6],
                    'updated_at': area[7]
                })
            
            return jsonify({
                'success': True,
                'data': research_data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'total_pages': total_pages
                }
            })
            
    except Exception as e:
        print(f"获取研究领域失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@research_bp.route('/api/research', methods=['POST'])
def create_research_area():
    """创建新的研究领域"""
    try:
        data = request.get_json()
        
        if not data or not data.get('title'):
            return jsonify({
                'success': False,
                'error': '标题不能为空'
            }), 400
        
        title = data.get('title', '').strip()
        category = data.get('category', '深度学习').strip()
        description = data.get('description', '').strip()
        members = data.get('members', [])
        
        # 验证数据
        if not title:
            return jsonify({
                'success': False,
                'error': '标题不能为空'
            }), 400
        
        with get_db() as conn:
            # 获取最大排序索引
            cursor = conn.execute('SELECT COALESCE(MAX(order_index), 0) FROM research_areas')
            max_order = cursor.fetchone()[0]
            
            # 插入新记录
            cursor = conn.execute('''
                INSERT INTO research_areas (title, category, description, members, order_index, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                title, category, description, 
                json.dumps(members, ensure_ascii=False), 
                max_order + 1,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            area_id = cursor.lastrowid
            conn.commit()
            
            # 通知前端更新
            notify_page_refresh('research', {
                'operation': 'created',
                'type': 'RESEARCH_DATA_UPDATED',
                'timestamp': datetime.now().timestamp() * 1000
            })
            
            return jsonify({
                'success': True,
                'message': '研究领域创建成功',
                'data': {
                    'id': area_id,
                    'title': title,
                    'category': category,
                    'description': description,
                    'members': members,
                    'order_index': max_order + 1
                }
            }), 201
            
    except Exception as e:
        print(f"创建研究领域失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@research_bp.route('/api/research/<int:area_id>', methods=['PUT'])
def update_research_area(area_id):
    """更新研究领域"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据不能为空'
            }), 400
        
        with get_db() as conn:
            # 检查记录是否存在
            cursor = conn.execute('SELECT * FROM research_areas WHERE id = ?', (area_id,))
            if not cursor.fetchone():
                return jsonify({
                    'success': False,
                    'error': '研究领域不存在'
                }), 404
            
            # 构建更新字段
            update_fields = []
            update_values = []
            
            if 'title' in data:
                title = data['title'].strip()
                if title:
                    update_fields.append('title = ?')
                    update_values.append(title)
            
            if 'category' in data:
                category = data['category'].strip()
                if category:
                    update_fields.append('category = ?')
                    update_values.append(category)
            
            if 'description' in data:
                description = data['description'].strip()
                update_fields.append('description = ?')
                update_values.append(description)
            
            if 'members' in data:
                members = data['members'] if isinstance(data['members'], list) else []
                update_fields.append('members = ?')
                update_values.append(json.dumps(members, ensure_ascii=False))
            
            if 'order_index' in data:
                order_index = int(data['order_index'])
                update_fields.append('order_index = ?')
                update_values.append(order_index)
            
            # 添加更新时间
            update_fields.append('updated_at = ?')
            update_values.append(datetime.now().isoformat())
            
            if not update_fields:
                return jsonify({
                    'success': False,
                    'error': '没有需要更新的字段'
                }), 400
            
            # 执行更新
            sql = f'UPDATE research_areas SET {", ".join(update_fields)} WHERE id = ?'
            update_values.append(area_id)
            
            conn.execute(sql, update_values)
            conn.commit()
            
            # 通知前端更新
            notify_page_refresh('research', {
                'operation': 'updated',
                'type': 'RESEARCH_DATA_UPDATED',
                'timestamp': datetime.now().timestamp() * 1000
            })
            
            return jsonify({
                'success': True,
                'message': '研究领域更新成功'
            })
            
    except Exception as e:
        print(f"更新研究领域失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@research_bp.route('/api/research/<int:area_id>', methods=['DELETE'])
def delete_research_area(area_id):
    """删除研究领域"""
    try:
        with get_db() as conn:
            # 检查记录是否存在
            cursor = conn.execute('SELECT * FROM research_areas WHERE id = ?', (area_id,))
            if not cursor.fetchone():
                return jsonify({
                    'success': False,
                    'error': '研究领域不存在'
                }), 404
            
            # 删除记录
            conn.execute('DELETE FROM research_areas WHERE id = ?', (area_id,))
            conn.commit()
            
            # 通知前端更新
            notify_page_refresh('research', {
                'operation': 'deleted',
                'type': 'RESEARCH_DATA_UPDATED',
                'timestamp': datetime.now().timestamp() * 1000
            })
            
            return jsonify({
                'success': True,
                'message': '研究领域删除成功'
            })
            
    except Exception as e:
        print(f"删除研究领域失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@research_bp.route('/api/research/reorder', methods=['POST'])
def reorder_research_areas():
    """重新排序研究领域"""
    try:
        data = request.get_json()
        area_ids = data.get('area_ids', [])
        
        if not area_ids or not isinstance(area_ids, list):
            return jsonify({
                'success': False,
                'error': '排序ID列表不能为空'
            }), 400
        
        with get_db() as conn:
            # 批量更新排序索引
            for index, area_id in enumerate(area_ids):
                conn.execute('UPDATE research_areas SET order_index = ? WHERE id = ?', (index + 1, area_id))
            
            conn.commit()
            
            # 通知前端更新
            notify_page_refresh('research', {
                'operation': 'reordered',
                'type': 'RESEARCH_DATA_UPDATED',
                'timestamp': datetime.now().timestamp() * 1000
            })
            
            return jsonify({
                'success': True,
                'message': '研究领域排序更新成功'
            })
            
    except Exception as e:
        print(f"重新排序研究领域失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@research_bp.route('/api/research/categories', methods=['GET'])
def get_research_categories():
    """获取研究领域分类列表"""
    try:
        with get_db() as conn:
            cursor = conn.execute('''
                SELECT DISTINCT category, COUNT(*) as count
                FROM research_areas
                GROUP BY category
                ORDER BY count DESC
            ''')
            
            categories = []
            for row in cursor.fetchall():
                categories.append({
                    'name': row[0],
                    'count': row[1]
                })
            
            return jsonify({
                'success': True,
                'data': categories
            })
            
    except Exception as e:
        print(f"获取研究领域分类失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@research_bp.route('/api/research/stats', methods=['GET'])
def get_research_stats():
    """获取研究领域统计信息"""
    try:
        with get_db() as conn:
            # 总数量
            cursor = conn.execute('SELECT COUNT(*) FROM research_areas')
            total = cursor.fetchone()[0]
            
            # 分类统计
            cursor = conn.execute('''
                SELECT category, COUNT(*) as count
                FROM research_areas
                GROUP BY category
                ORDER BY count DESC
            ''')
            
            category_stats = {}
            for row in cursor.fetchall():
                category_stats[row[0]] = row[1]
            
            return jsonify({
                'success': True,
                'data': {
                    'total': total,
                    'categories': category_stats
                }
            })
            
    except Exception as e:
        print(f"获取研究领域统计失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 