"""
Socket.IO 工具模块
用于处理实时通知功能，避免循环导入问题
"""

from flask_socketio import emit
from flask import current_app

def notify_page_refresh(page, data):
    """
    通知指定页面刷新
    
    Args:
        page (str): 页面类型 ('home', 'team', 'papers', 'innovation', 'dynamic')
        data (dict): 要发送的数据
    """
    try:
        from flask import current_app
        socketio = current_app.extensions.get('socketio')
        if socketio:
            # 发送到特定房间
            socketio.emit('page_refresh', {
                'page': page,
                'type': 'data_updated',
                'payload': data
            }, room=page)
            
            # 同时发送到所有连接的客户端（作为备用）
            socketio.emit('page_refresh', {
                'page': 'all',
                'type': 'data_updated',
                'payload': data
            })
            
            print(f"已发送页面刷新通知到 {page}: {data}")
        else:
            print("SocketIO未初始化")
    except Exception as e:
        print(f"发送页面刷新通知失败: {e}")
        import traceback
        traceback.print_exc()

def notify_all_pages(data):
    """
    通知所有页面刷新
    
    Args:
        data (dict): 要发送的数据
    """
    try:
        from flask import current_app
        socketio = current_app.extensions.get('socketio')
        if socketio:
            socketio.emit('page_refresh', {
                'page': 'all',
                'type': 'data_updated',
                'payload': data
            })
            print(f"已发送全局页面刷新通知: {data}")
    except Exception as e:
        print(f"发送全局页面刷新通知失败: {e}")

def notify_team_update(data):
    """通知团队成员更新"""
    notify_page_refresh('team', data)
    notify_page_refresh('home', data)

def notify_papers_update(data):
    """通知论文更新"""
    notify_page_refresh('papers', data)
    notify_page_refresh('home', data)

def notify_innovation_update(data):
    """通知创新项目更新"""
    notify_page_refresh('innovation', data)
    notify_page_refresh('home', data)

def notify_dynamic_update(data):
    """通知动态更新"""
    notify_page_refresh('dynamic', data)
    notify_page_refresh('home', data)

def notify_algorithms_update(data):
    """通知算法更新"""
    notify_page_refresh('algorithms', data)
    notify_page_refresh('home', data)