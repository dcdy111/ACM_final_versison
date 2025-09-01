#!/usr/bin/env python3
"""
年级管理API
实现年级的增删改查和排序功能
"""

from flask import Blueprint, request, jsonify, session
from db_utils import get_db
from socket_utils import notify_page_refresh
import logging
import json

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

grades_bp = Blueprint('grades', __name__)

@grades_bp.route('/api/grades', methods=['GET'])
def get_grades():
    """获取所有年级"""
    try:
        with get_db() as conn:
            # 获取所有年级，按order_index排序
            rows = conn.execute('''
                SELECT id, name, description, order_index, created_at, updated_at
                FROM grades 
                ORDER BY order_index ASC, created_at DESC
            ''').fetchall()
            
            grades = []
            for row in rows:
                # 获取该年级的成员数量
                member_count = conn.execute('''
                    SELECT COUNT(*) as count FROM team_members WHERE grade = ?
                ''', (row['name'],)).fetchone()['count']
                
                grades.append({
                    'id': row['id'],
                    'name': row['name'],
                    'description': row['description'],
                    'member_count': member_count,
                    'order_index': row['order_index'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })
            
            logger.info(f"获取年级成功，共{len(grades)}个年级")
            return jsonify(grades), 200
    except Exception as e:
        logger.error(f"获取年级失败: {e}")
        return jsonify({'error': '获取年级失败'}), 500

@grades_bp.route('/api/grades', methods=['POST'])
def create_grade():
    """创建新年级"""
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({"error": "未授权"}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据为空"}), 400
        
        name = str(data.get('name', '')).strip()
        description = str(data.get('description', '')).strip()
        
        if not name:
            return jsonify({"error": "年级名称不能为空"}), 400
        
        # 验证年级格式（YYYY级）
        if not name.endswith('级') or len(name) != 5:
            return jsonify({"error": "年级格式不正确，应为YYYY级格式"}), 400
        
        try:
            year = int(name[:4])
            if year < 1900 or year > 2100:
                return jsonify({"error": "年级年份不合理"}), 400
        except ValueError:
            return jsonify({"error": "年级格式不正确，应为YYYY级格式"}), 400
        
        with get_db() as conn:
            # 检查年级是否已存在
            existing = conn.execute('SELECT id FROM grades WHERE name = ?', (name,)).fetchone()
            if existing:
                return jsonify({"error": "该年级已存在"}), 400
            
            # 获取当前最大排序索引
            max_order = conn.execute('SELECT MAX(order_index) as max_order FROM grades').fetchone()
            new_order = (max_order['max_order'] or 0) + 1
            
            cursor = conn.execute('''
                INSERT INTO grades (name, description, order_index)
                VALUES (?, ?, ?)
            ''', (name, description, new_order))
            
            grade_id = cursor.lastrowid
            conn.commit()
            
            # 返回新创建的年级信息
            grade_data = {
                'id': grade_id,
                'name': name,
                'description': description,
                'member_count': 0,
                'order_index': new_order,
                'created_at': None,
                'updated_at': None
            }
            
            # 发送实时通知到前端页面
            notify_page_refresh('team', {
                'grade_created': True,
                'grade_id': grade_id,
                'grade_data': grade_data
            })
            notify_page_refresh('home', {
                'grade_created': True,
                'grade_id': grade_id
            })
            
            logger.info(f"创建年级成功: {name}")
            return jsonify(grade_data), 201
        
    except Exception as e:
        logger.error(f"创建年级失败: {e}")
        return jsonify({'error': '创建年级失败'}), 500

@grades_bp.route('/api/grades/<int:grade_id>', methods=['PUT'])
def update_grade(grade_id):
    """更新年级信息"""
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({"error": "未授权"}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据为空"}), 400
        
        name = str(data.get('name', '')).strip()
        description = str(data.get('description', '')).strip()
        
        if not name:
            return jsonify({"error": "年级名称不能为空"}), 400
        
        # 验证年级格式（YYYY级）
        if not name.endswith('级') or len(name) != 5:
            return jsonify({"error": "年级格式不正确，应为YYYY级格式"}), 400
        
        try:
            year = int(name[:4])
            if year < 1900 or year > 2100:
                return jsonify({"error": "年级年份不合理"}), 400
        except ValueError:
            return jsonify({"error": "年级格式不正确，应为YYYY级格式"}), 400
        
        with get_db() as conn:
            # 先获取当前年级信息
            current_grade = conn.execute('SELECT name FROM grades WHERE id = ?', (grade_id,)).fetchone()
            if not current_grade:
                return jsonify({"error": "年级不存在"}), 404
            
            current_name = current_grade['name']
            
            # 如果名称没有改变，不需要检查冲突
            if name == current_name:
                pass
            else:
                # 检查年级是否已存在（排除当前年级）
                existing = conn.execute('SELECT id FROM grades WHERE name = ? AND id != ?', (name, grade_id)).fetchone()
                if existing:
                    return jsonify({"error": "该年级名称已存在"}), 400
            
            # 更新年级信息
            conn.execute('''
                UPDATE grades 
                SET name = ?, description = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (name, description, grade_id))
            
            # 如果年级名称改变了，同时更新团队成员表中的年级字段
            if name != current_name:
                conn.execute('''
                    UPDATE team_members 
                    SET grade = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE grade = ?
                ''', (name, current_name))
            
            conn.commit()
            
            # 获取更新后的年级信息
            updated_grade = conn.execute('''
                SELECT id, name, description, order_index, created_at, updated_at
                FROM grades WHERE id = ?
            ''', (grade_id,)).fetchone()
            
            if not updated_grade:
                return jsonify({"error": "年级不存在"}), 404
            
            # 获取该年级的成员数量
            member_count = conn.execute('''
                SELECT COUNT(*) as count FROM team_members WHERE grade = ?
            ''', (name,)).fetchone()['count']
            
            grade_data = {
                'id': updated_grade['id'],
                'name': updated_grade['name'],
                'description': updated_grade['description'],
                'member_count': member_count,
                'order_index': updated_grade['order_index'],
                'created_at': updated_grade['created_at'],
                'updated_at': updated_grade['updated_at']
            }
            
            # 发送实时通知到前端页面
            notify_page_refresh('team', {
                'grade_updated': True,
                'grade_id': grade_id,
                'grade_data': grade_data
            })
            notify_page_refresh('home', {
                'grade_updated': True,
                'grade_id': grade_id
            })
            
            logger.info(f"更新年级成功: {name}")
            return jsonify(grade_data), 200
        
    except Exception as e:
        logger.error(f"更新年级失败: {e}")
        return jsonify({'error': '更新年级失败'}), 500

@grades_bp.route('/api/grades/<int:grade_id>', methods=['DELETE'])
def delete_grade(grade_id):
    """删除年级"""
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({"error": "未授权"}), 401
    
    try:
        with get_db() as conn:
            # 获取年级信息
            grade = conn.execute('SELECT name FROM grades WHERE id = ?', (grade_id,)).fetchone()
            if not grade:
                return jsonify({"error": "年级不存在"}), 404
            
            grade_name = grade['name']
            
            # 检查是否有成员属于该年级
            member_count = conn.execute('''
                SELECT COUNT(*) as count FROM team_members WHERE grade = ?
            ''', (grade_name,)).fetchone()['count']
            
            if member_count > 0:
                return jsonify({"error": f"该年级下还有{member_count}名成员，无法删除"}), 400
            
            # 删除年级
            conn.execute('DELETE FROM grades WHERE id = ?', (grade_id,))
            conn.commit()
            
            # 发送实时通知到前端页面
            notify_page_refresh('team', {
                'grade_deleted': True,
                'grade_id': grade_id,
                'grade_name': grade_name
            })
            notify_page_refresh('home', {
                'grade_deleted': True,
                'grade_id': grade_id
            })
            
            logger.info(f"删除年级成功: {grade_name}")
            return jsonify({"message": "年级删除成功"}), 200
        
    except Exception as e:
        logger.error(f"删除年级失败: {e}")
        return jsonify({'error': '删除年级失败'}), 500

@grades_bp.route('/api/grades/reorder', methods=['POST'])
def reorder_grades():
    """重新排序年级"""
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({"error": "未授权"}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据为空"}), 400
        
        grade_ids = data.get('grade_ids', [])
        if not isinstance(grade_ids, list) or len(grade_ids) == 0:
            return jsonify({"error": "年级ID列表不能为空"}), 400
        
        with get_db() as conn:
            # 更新年级排序
            for index, grade_id in enumerate(grade_ids):
                conn.execute('''
                    UPDATE grades 
                    SET order_index = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (index + 1, grade_id))
            
            conn.commit()
            
            # 发送实时通知到前端页面
            notify_page_refresh('team', {
                'grade_reordered': True,
                'grade_ids': grade_ids
            })
            notify_page_refresh('home', {
                'grade_reordered': True,
                'grade_ids': grade_ids
            })
            
            logger.info(f"年级排序更新成功，共{len(grade_ids)}个年级")
            return jsonify({"message": "年级排序更新成功"}), 200
        
    except Exception as e:
        logger.error(f"更新年级排序失败: {e}")
        return jsonify({'error': '更新年级排序失败'}), 500 