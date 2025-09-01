# 研究领域API - 提供研究领域的CRUD操作和实时同步

from flask import Blueprint, request, jsonify
from db_utils import get_db
import json
import os
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
        
        # 检查是否在 Vercel 环境中
        if os.environ.get('VERCEL'):
            # Vercel 环境：返回Mock数据
            mock_research_data = [
                {
                    'id': 1,
                    'title': '机器学习与深度学习',
                    'category': '人工智能',
                    'description': '研究深度神经网络、强化学习、计算机视觉等前沿技术，致力于将AI技术应用于实际问题解决。',
                    'members': ['张教授', '李博士', '王同学'],
                    'order_index': 1,
                    'created_at': '2024-01-01T00:00:00Z',
                    'updated_at': '2024-01-01T00:00:00Z'
                },
                {
                    'id': 2,
                    'title': '算法设计与优化',
                    'category': '理论计算机科学',
                    'description': '专注于算法复杂度分析、数据结构优化、并行计算等理论与实践相结合的研究。',
                    'members': ['陈教授', '刘同学'],
                    'order_index': 2,
                    'created_at': '2024-01-02T00:00:00Z',
                    'updated_at': '2024-01-02T00:00:00Z'
                },
                {
                    'id': 3,
                    'title': '自然语言处理',
                    'category': '人工智能',
                    'description': '研究文本理解、语言生成、对话系统等NLP技术，推动人机交互的自然化发展。',
                    'members': ['赵教授', '钱同学', '孙同学'],
                    'order_index': 3,
                    'created_at': '2024-01-03T00:00:00Z',
                    'updated_at': '2024-01-03T00:00:00Z'
                },
                {
                    'id': 4,
                    'title': '大数据分析',
                    'category': '数据科学',
                    'description': '利用统计学习、数据挖掘等技术处理海量数据，发现数据中的规律和价值。',
                    'members': ['周教授', '吴同学'],
                    'order_index': 4,
                    'created_at': '2024-01-04T00:00:00Z',
                    'updated_at': '2024-01-04T00:00:00Z'
                },
                {
                    'id': 5,
                    'title': '计算机视觉',
                    'category': '人工智能',
                    'description': '研究图像识别、目标检测、图像生成等计算机视觉技术及其在各领域的应用。',
                    'members': ['郑教授', '冯同学', '陈同学'],
                    'order_index': 5,
                    'created_at': '2024-01-05T00:00:00Z',
                    'updated_at': '2024-01-05T00:00:00Z'
                },
                {
                    'id': 6,
                    'title': '软件工程与系统设计',
                    'category': '软件工程',
                    'description': '专注于大型软件系统架构设计、开发流程优化、软件质量保证等工程实践。',
                    'members': ['何教授', '许同学'],
                    'order_index': 6,
                    'created_at': '2024-01-06T00:00:00Z',
                    'updated_at': '2024-01-06T00:00:00Z'
                }
            ]
            
            # 分类筛选
            if category and category != '全部':
                mock_research_data = [item for item in mock_research_data if item['category'] == category]
            
            # 计算分页
            total = len(mock_research_data)
            total_pages = (total + per_page - 1) // per_page
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_data = mock_research_data[start_idx:end_idx]
            
            print(f"🔧 Vercel环境：返回研究领域Mock数据 {len(paginated_data)} 个")
            return jsonify({
                'success': True,
                'data': paginated_data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'total_pages': total_pages
                }
            })
        
        # 本地环境：正常数据库查询
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