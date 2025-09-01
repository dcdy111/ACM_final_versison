#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动备份脚本
定期备份ACM实验室系统数据，确保数据安全
"""

import os
import shutil
import sqlite3
import json
import schedule
import time
from datetime import datetime, timedelta
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DATABASE = 'acm_lab.db'
BACKUP_DIR = 'data_backups'
MAX_BACKUPS = 10  # 保留最近10个备份

def ensure_backup_dir():
    """确保备份目录存在"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        logger.info(f"创建备份目录: {BACKUP_DIR}")

def cleanup_old_backups():
    """清理过期的备份文件"""
    try:
        ensure_backup_dir()
        
        # 获取所有备份文件
        backup_files = []
        for file in os.listdir(BACKUP_DIR):
            if file.startswith('acm_lab_backup_') and file.endswith('.db'):
                file_path = os.path.join(BACKUP_DIR, file)
                backup_files.append((file_path, os.path.getctime(file_path)))
        
        # 按创建时间排序
        backup_files.sort(key=lambda x: x[1], reverse=True)
        
        # 删除超过MAX_BACKUPS的文件
        if len(backup_files) > MAX_BACKUPS:
            for file_path, _ in backup_files[MAX_BACKUPS:]:
                os.remove(file_path)
                logger.info(f"删除过期备份: {os.path.basename(file_path)}")
                
    except Exception as e:
        logger.error(f"清理备份文件失败: {e}")

def backup_database():
    """备份数据库"""
    try:
        if not os.path.exists(DATABASE):
            logger.warning(f"数据库文件不存在: {DATABASE}")
            return False
            
        ensure_backup_dir()
        
        # 生成备份文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(BACKUP_DIR, f'acm_lab_backup_{timestamp}.db')
        
        # 复制数据库文件
        shutil.copy2(DATABASE, backup_file)
        
        # 验证备份文件
        if os.path.exists(backup_file):
            file_size = os.path.getsize(backup_file) / 1024  # KB
            logger.info(f"数据库备份成功: {backup_file} ({file_size:.1f} KB)")
            
            # 清理旧备份
            cleanup_old_backups()
            return True
        else:
            logger.error("备份文件创建失败")
            return False
            
    except Exception as e:
        logger.error(f"数据库备份失败: {e}")
        return False

def get_database_info():
    """获取数据库信息"""
    try:
        if not os.path.exists(DATABASE):
            return None
            
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        
        # 获取表统计信息
        tables_info = {}
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            try:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                tables_info[table] = count
            except:
                tables_info[table] = 0
        
        conn.close()
        
        return {
            'file_size': os.path.getsize(DATABASE) / 1024,  # KB
            'tables': tables_info,
            'total_records': sum(tables_info.values())
        }
        
    except Exception as e:
        logger.error(f"获取数据库信息失败: {e}")
        return None

def scheduled_backup():
    """定时备份任务"""
    logger.info("开始执行定时备份任务")
    
    # 获取备份前的数据库信息
    db_info = get_database_info()
    if db_info:
        logger.info(f"数据库信息: {db_info['total_records']} 条记录, {db_info['file_size']:.1f} KB")
    
    # 执行备份
    success = backup_database()
    
    if success:
        logger.info("定时备份任务完成")
    else:
        logger.error("定时备份任务失败")

def manual_backup():
    """手动备份"""
    print("🚀 开始手动备份...")
    
    db_info = get_database_info()
    if db_info:
        print(f"📊 数据库信息:")
        print(f"   文件大小: {db_info['file_size']:.1f} KB")
        print(f"   总记录数: {db_info['total_records']}")
        print(f"   表详情:")
        for table, count in db_info['tables'].items():
            if count > 0:
                print(f"      {table}: {count} 条")
    
    success = backup_database()
    
    if success:
        print("✅ 手动备份完成！")
        
        # 显示备份文件列表
        print(f"\n📁 备份文件列表:")
        backup_files = []
        for file in os.listdir(BACKUP_DIR):
            if file.startswith('acm_lab_backup_') and file.endswith('.db'):
                file_path = os.path.join(BACKUP_DIR, file)
                file_size = os.path.getsize(file_path) / 1024
                create_time = datetime.fromtimestamp(os.path.getctime(file_path))
                backup_files.append((file, file_size, create_time))
        
        backup_files.sort(key=lambda x: x[2], reverse=True)
        for i, (file, size, time) in enumerate(backup_files[:5], 1):
            print(f"   {i}. {file} ({size:.1f} KB) - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("❌ 手动备份失败！")

def start_scheduler():
    """启动定时备份调度器"""
    # 每天凌晨2点备份
    schedule.every().day.at("02:00").do(scheduled_backup)
    
    # 每12小时备份一次
    schedule.every(12).hours.do(scheduled_backup)
    
    logger.info("备份调度器已启动")
    logger.info("定时任务: 每天凌晨2点 和 每12小时执行备份")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
    except KeyboardInterrupt:
        logger.info("备份调度器已停止")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ACM实验室数据库自动备份工具')
    parser.add_argument('action', nargs='?', choices=['backup', 'schedule', 'info'], 
                       default='backup', help='执行的操作')
    
    args = parser.parse_args()
    
    if args.action == 'backup':
        manual_backup()
    elif args.action == 'schedule':
        start_scheduler()
    elif args.action == 'info':
        db_info = get_database_info()
        if db_info:
            print(f"📊 数据库信息:")
            print(f"   文件: {DATABASE}")
            print(f"   大小: {db_info['file_size']:.1f} KB")
            print(f"   总记录: {db_info['total_records']}")
            print(f"   表统计:")
            for table, count in sorted(db_info['tables'].items()):
                if count > 0:
                    print(f"      {table}: {count} 条")
        else:
            print("❌ 无法获取数据库信息")

if __name__ == '__main__':
    main()
