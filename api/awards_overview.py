from flask import Blueprint, request, jsonify, abort, session
from db_utils import get_db
from datetime import datetime
import traceback

# 创建算法蓝图
algorithm_bp = Blueprint('algorithm', __name__, url_prefix='/api')



@algorithm_bp.route('/frontend/algorithm-awards', methods=['GET'])
def get_frontend_algorithm_awards():
    """获取竞赛获奖记录（前端展示）"""
    try:
        with get_db() as conn:
            # 获取启用的获奖记录，按排序索引和创建时间排序
            cursor = conn.execute('''
                SELECT * FROM algorithm_awards 
                WHERE status = 'active'
                ORDER BY COALESCE(order_index, 0) ASC, created_at DESC
            ''')
            awards = cursor.fetchall()
            
            # 转换为字典格式
            awards_data = [dict(award) for award in awards]
            
            return jsonify(awards_data)
    except Exception as e:
        print(f"Error fetching frontend algorithm awards: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@algorithm_bp.route('/frontend/project-overview', methods=['GET'])
def get_frontend_project_overview():
    """获取项目概览统计（前端展示）"""
    try:
        with get_db() as conn:
            # 获取启用的统计项，按排序索引和创建时间排序
            cursor = conn.execute('''
                SELECT * FROM project_overview 
                WHERE status = 'active'
                ORDER BY COALESCE(order_index, 0) ASC, created_at DESC
            ''')
            overviews = cursor.fetchall()
            
            # 转换为字典格式
            overviews_data = [dict(overview) for overview in overviews]
            
            return jsonify(overviews_data)
    except Exception as e:
        print(f"Error fetching frontend project overview: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500













# 算法竞赛获奖记录管理API
@algorithm_bp.route('/admin/algorithm-awards', methods=['GET'])
def get_admin_algorithm_awards():
    """获取所有竞赛获奖记录（管理后台）"""
    try:
        print("🔍 开始获取获奖记录数据...")
        with get_db() as conn:
            cursor = conn.execute('''
                SELECT * FROM algorithm_awards 
                ORDER BY COALESCE(order_index, 0) ASC, created_at DESC
            ''')
            awards = cursor.fetchall()
            
            result = []
            for award in awards:
                award_dict = dict(award)
                result.append(award_dict)
            
        print(f"✅ 成功获取 {len(result)} 个获奖记录")
        return jsonify(result)
    except Exception as e:
        print(f"❌ 获取获奖记录数据失败: {e}")
        return jsonify({'error': str(e)}), 500

@algorithm_bp.route('/admin/algorithm-awards', methods=['POST'])
def create_admin_algorithm_award():
    """创建新竞赛获奖记录"""
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({"error": "未授权"}), 401
    
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('title') or not data.get('competition_name') or not data.get('award_level'):
            return jsonify({'error': '标题、竞赛名称和获奖等级为必填字段'}), 400
        
        title = str(data['title']).strip()
        competition_name = str(data['competition_name']).strip()
        award_level = str(data['award_level']).strip()
        winner_name = str(data.get('winner_name', '')).strip()
        competition_date = data.get('competition_date', '')
        competition_location = str(data.get('competition_location', '')).strip()
        team_score = str(data.get('team_score', '')).strip()
        image_url = str(data.get('image_url', '')).strip()
        description = str(data.get('description', '')).strip()
        status = str(data.get('status', 'active')).strip()
        
        with get_db() as conn:
            # 获取最大排序索引
            cursor = conn.execute('SELECT COALESCE(MAX(order_index), 0) FROM algorithm_awards')
            max_order = cursor.fetchone()[0]
            
            # 插入新获奖记录
            cursor = conn.execute('''
                INSERT INTO algorithm_awards (title, competition_name, award_level, winner_name,
                                            competition_date, competition_location, team_score,
                                            image_url, description, status, order_index,
                                            created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                title, competition_name, award_level, winner_name, competition_date,
                competition_location, team_score, image_url, description, status,
                max_order + 1, datetime.now().isoformat(), datetime.now().isoformat()
            ))
            
            award_id = cursor.lastrowid
            conn.commit()
            
            print(f"✅ 竞赛获奖记录创建成功: {title}")
            
            return jsonify({
                'success': True,
                'message': '竞赛获奖记录创建成功',
                'award_id': award_id
            }), 201
    except Exception as e:
        print(f"Error creating algorithm award: {e}")
        return jsonify({'error': f'创建竞赛获奖记录失败: {str(e)}'}), 500

@algorithm_bp.route('/admin/algorithm-awards/<int:award_id>', methods=['GET'])
def get_admin_algorithm_award_detail(award_id):
    """获取单个竞赛获奖记录"""
    try:
        with get_db() as conn:
            cursor = conn.execute('SELECT * FROM algorithm_awards WHERE id = ?', (award_id,))
            award = cursor.fetchone()
            if not award:
                return jsonify({'error': '竞赛获奖记录不存在'}), 404
            
            return jsonify({
                'success': True,
                'award': dict(award)
            })
    except Exception as e:
        print(f"Error fetching algorithm award: {e}")
        return jsonify({'error': f'获取竞赛获奖记录失败: {str(e)}'}), 500

@algorithm_bp.route('/admin/algorithm-awards/<int:award_id>', methods=['PUT'])
def update_admin_algorithm_award(award_id):
    """更新竞赛获奖记录"""
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({"error": "未授权"}), 401
    
    try:
        data = request.get_json()
        
        with get_db() as conn:
            # 检查获奖记录是否存在
            cursor = conn.execute('SELECT * FROM algorithm_awards WHERE id = ?', (award_id,))
            if not cursor.fetchone():
                return jsonify({'error': '竞赛获奖记录不存在'}), 404
            
            # 构建更新字段
            update_fields = []
            update_values = []
            
            # 更新字段
            if 'title' in data:
                update_fields.append('title = ?')
                update_values.append(str(data['title']).strip())
            if 'competition_name' in data:
                update_fields.append('competition_name = ?')
                update_values.append(str(data['competition_name']).strip())
            if 'award_level' in data:
                update_fields.append('award_level = ?')
                update_values.append(str(data['award_level']).strip())
            if 'winner_name' in data:
                update_fields.append('winner_name = ?')
                update_values.append(str(data['winner_name']).strip())
            if 'competition_date' in data:
                update_fields.append('competition_date = ?')
                update_values.append(data['competition_date'])
            if 'competition_location' in data:
                update_fields.append('competition_location = ?')
                update_values.append(str(data['competition_location']).strip())
            if 'team_score' in data:
                update_fields.append('team_score = ?')
                update_values.append(str(data['team_score']).strip())
            if 'image_url' in data:
                update_fields.append('image_url = ?')
                update_values.append(str(data['image_url']).strip())
            if 'description' in data:
                update_fields.append('description = ?')
                update_values.append(str(data['description']).strip())
            if 'status' in data:
                update_fields.append('status = ?')
                update_values.append(str(data['status']).strip())
            if 'order_index' in data:
                update_fields.append('order_index = ?')
                update_values.append(int(data['order_index']))
            
            # 添加更新时间
            update_fields.append('updated_at = ?')
            update_values.append(datetime.now().isoformat())
            
            # 添加获奖记录ID到值列表
            update_values.append(award_id)
            
            # 执行更新
            if update_fields:
                sql = f'UPDATE algorithm_awards SET {", ".join(update_fields)} WHERE id = ?'
                conn.execute(sql, update_values)
                conn.commit()
                
                print(f"✅ 竞赛获奖记录更新成功: ID={award_id}")
                
                return jsonify({
                    'success': True,
                    'message': '竞赛获奖记录更新成功'
                })
            else:
                return jsonify({'error': '没有需要更新的字段'}), 400
                
    except Exception as e:
        print(f"Error updating algorithm award: {e}")
        return jsonify({'error': f'更新竞赛获奖记录失败: {str(e)}'}), 500

@algorithm_bp.route('/admin/algorithm-awards/<int:award_id>', methods=['DELETE'])
def delete_admin_algorithm_award(award_id):
    """删除竞赛获奖记录"""
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({"error": "未授权"}), 401
    
    try:
        with get_db() as conn:
            # 检查获奖记录是否存在
            cursor = conn.execute('SELECT * FROM algorithm_awards WHERE id = ?', (award_id,))
            award = cursor.fetchone()
            if not award:
                return jsonify({'error': '竞赛获奖记录不存在'}), 404
            
            # 删除获奖记录
            conn.execute('DELETE FROM algorithm_awards WHERE id = ?', (award_id,))
            conn.commit()
            
            print(f"✅ 竞赛获奖记录删除成功: {award['title']}")
            
            return jsonify({
                'success': True,
                'message': '竞赛获奖记录删除成功'
            })
    except Exception as e:
        print(f"Error deleting algorithm award: {e}")
        return jsonify({'error': f'删除竞赛获奖记录失败: {str(e)}'}), 500

@algorithm_bp.route('/admin/algorithm-awards/reorder', methods=['PUT'])
def reorder_admin_algorithm_awards():
    """重新排序竞赛获奖记录"""
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({"error": "未授权"}), 401
    
    try:
        data = request.get_json()
        order_data = data.get('order', [])
        
        if not order_data:
            return jsonify({'error': '缺少排序数据'}), 400
        
        with get_db() as conn:
            for item in order_data:
                award_id = item.get('id')
                order_index = item.get('order_index', 0)
                
                if award_id:
                    conn.execute('UPDATE algorithm_awards SET order_index = ? WHERE id = ?', (order_index, award_id))
            
            conn.commit()
            
            print(f"✅ 竞赛获奖记录排序更新成功")
            
            return jsonify({
                'success': True,
                'message': '竞赛获奖记录排序更新成功'
            })
    except Exception as e:
        print(f"Error reordering algorithm awards: {e}")
        return jsonify({'error': f'更新竞赛获奖记录排序失败: {str(e)}'}), 500

# 项目概览管理API
@algorithm_bp.route('/admin/project-overview', methods=['GET'])
def get_admin_project_overview():
    """获取所有项目概览统计（管理后台）"""
    try:
        print("🔍 开始获取项目概览数据...")
        with get_db() as conn:
            cursor = conn.execute('''
                SELECT * FROM project_overview 
                ORDER BY COALESCE(order_index, 0) ASC, created_at DESC
            ''')
            overviews = cursor.fetchall()
            
            result = []
            for overview in overviews:
                overview_dict = dict(overview)
                result.append(overview_dict)
            
        print(f"✅ 成功获取 {len(result)} 个项目概览")
        return jsonify(result)
    except Exception as e:
        print(f"❌ 获取项目概览数据失败: {e}")
        return jsonify({'error': str(e)}), 500

@algorithm_bp.route('/admin/project-overview', methods=['POST'])
def create_admin_project_overview():
    """创建新项目概览统计"""
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({"error": "未授权"}), 401
    
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('name') or not data.get('value'):
            return jsonify({'error': '名称和数值为必填字段'}), 400
        
        name = str(data['name']).strip()
        value = str(data['value']).strip()
        icon = str(data.get('icon', '')).strip()
        description = str(data.get('description', '')).strip()
        status = str(data.get('status', 'active')).strip()
        
        with get_db() as conn:
            # 获取最大排序索引
            cursor = conn.execute('SELECT COALESCE(MAX(order_index), 0) FROM project_overview')
            max_order = cursor.fetchone()[0]
            
            # 插入新项目概览统计
            cursor = conn.execute('''
                INSERT INTO project_overview (name, value, icon, description, status, 
                                           order_index, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                name, value, icon, description, status, max_order + 1,
                datetime.now().isoformat(), datetime.now().isoformat()
            ))
            
            overview_id = cursor.lastrowid
            conn.commit()
            
            print(f"✅ 项目概览统计创建成功: {name}")
            
            return jsonify({
                'success': True,
                'message': '项目概览统计创建成功',
                'overview_id': overview_id
            }), 201
    except Exception as e:
        print(f"Error creating project overview: {e}")
        return jsonify({'error': f'创建项目概览统计失败: {str(e)}'}), 500

@algorithm_bp.route('/admin/project-overview/<int:overview_id>', methods=['GET'])
def get_admin_project_overview_detail(overview_id):
    """获取单个项目概览统计"""
    try:
        with get_db() as conn:
            cursor = conn.execute('SELECT * FROM project_overview WHERE id = ?', (overview_id,))
            overview = cursor.fetchone()
            if not overview:
                return jsonify({'error': '项目概览统计不存在'}), 404
            
            return jsonify({
                'success': True,
                'overview': dict(overview)
            })
    except Exception as e:
        print(f"Error fetching project overview: {e}")
        return jsonify({'error': f'获取项目概览统计失败: {str(e)}'}), 500

@algorithm_bp.route('/admin/project-overview/<int:overview_id>', methods=['PUT'])
def update_admin_project_overview(overview_id):
    """更新项目概览统计"""
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({"error": "未授权"}), 401
    
    try:
        data = request.get_json()
        
        with get_db() as conn:
            # 检查项目概览统计是否存在
            cursor = conn.execute('SELECT * FROM project_overview WHERE id = ?', (overview_id,))
            if not cursor.fetchone():
                return jsonify({'error': '项目概览统计不存在'}), 404
            
            # 构建更新字段
            update_fields = []
            update_values = []
            
            # 更新字段
            if 'name' in data:
                update_fields.append('name = ?')
                update_values.append(str(data['name']).strip())
            if 'value' in data:
                update_fields.append('value = ?')
                update_values.append(str(data['value']).strip())
            if 'icon' in data:
                update_fields.append('icon = ?')
                update_values.append(str(data['icon']).strip())
            if 'description' in data:
                update_fields.append('description = ?')
                update_values.append(str(data['description']).strip())
            if 'status' in data:
                update_fields.append('status = ?')
                update_values.append(str(data['status']).strip())
            if 'order_index' in data:
                update_fields.append('order_index = ?')
                update_values.append(int(data['order_index']))
            
            # 添加更新时间
            update_fields.append('updated_at = ?')
            update_values.append(datetime.now().isoformat())
            
            # 添加项目概览统计ID到值列表
            update_values.append(overview_id)
            
            # 执行更新
            if update_fields:
                sql = f'UPDATE project_overview SET {", ".join(update_fields)} WHERE id = ?'
                conn.execute(sql, update_values)
                conn.commit()
                
                print(f"✅ 项目概览统计更新成功: ID={overview_id}")
                
                return jsonify({
                    'success': True,
                    'message': '项目概览统计更新成功'
                })
            else:
                return jsonify({'error': '没有需要更新的字段'}), 400
                
    except Exception as e:
        print(f"Error updating project overview: {e}")
        return jsonify({'error': f'更新项目概览统计失败: {str(e)}'}), 500

@algorithm_bp.route('/admin/project-overview/<int:overview_id>', methods=['DELETE'])
def delete_admin_project_overview(overview_id):
    """删除项目概览统计"""
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({"error": "未授权"}), 401
    
    try:
        with get_db() as conn:
            # 检查项目概览统计是否存在
            cursor = conn.execute('SELECT * FROM project_overview WHERE id = ?', (overview_id,))
            overview = cursor.fetchone()
            if not overview:
                return jsonify({'error': '项目概览统计不存在'}), 404
            
            # 删除项目概览统计
            conn.execute('DELETE FROM project_overview WHERE id = ?', (overview_id,))
            conn.commit()
            
            print(f"✅ 项目概览统计删除成功: {overview['name']}")
            
            return jsonify({
                'success': True,
                'message': '项目概览统计删除成功'
            })
    except Exception as e:
        print(f"Error deleting project overview: {e}")
        return jsonify({'error': f'删除项目概览统计失败: {str(e)}'}), 500

@algorithm_bp.route('/admin/project-overview/reorder', methods=['PUT'])
def reorder_admin_project_overview():
    """重新排序项目概览统计"""
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({"error": "未授权"}), 401
    
    try:
        data = request.get_json()
        order_data = data.get('order', [])
        
        if not order_data:
            return jsonify({'error': '缺少排序数据'}), 400
        
        with get_db() as conn:
            for item in order_data:
                overview_id = item.get('id')
                order_index = item.get('order_index', 0)
                
                if overview_id:
                    conn.execute('UPDATE project_overview SET order_index = ? WHERE id = ?', (order_index, overview_id))
            
            conn.commit()
            
            print(f"✅ 项目概览统计排序更新成功")
            
            return jsonify({
                'success': True,
                'message': '项目概览统计排序更新成功'
            })
    except Exception as e:
        print(f"Error reordering project overview: {e}")
        return jsonify({'error': f'更新项目概览统计排序失败: {str(e)}'}), 500 