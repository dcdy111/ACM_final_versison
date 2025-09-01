// Socket.IO客户端脚本
let socket = null;
// 避免重复声明currentPage变量，使用window.currentPage或检查是否已存在
if (typeof window.currentPage === 'undefined') {
    window.currentPage = null;
}
let reconnectAttempts = 0;
let maxReconnectAttempts = 10;
let reconnectDelay = 2000;
let isConnecting = false;

// 初始化Socket.IO连接 - 优化版本
function initSocketIO() {
    // 检查是否已经存在连接或正在连接
    if (socket && (socket.connected || isConnecting)) {
        return;
    }
    
    // 防止重复初始化
    if (isConnecting) {
        return;
    }
    
    isConnecting = true;
    
    try {
        // 创建Socket.IO连接，优化配置 - 提高响应速度
        socket = io({
            transports: ['websocket', 'polling'],
            timeout: 15000, // 减少超时时间，提高响应速度
            reconnection: true,
            reconnectionAttempts: maxReconnectAttempts,
            reconnectionDelay: 1000, // 减少重连延迟
            reconnectionDelayMax: 5000, // 减少最大重连延迟
            maxReconnectionAttempts: maxReconnectAttempts,
            forceNew: false,
            autoConnect: true,
            upgrade: true, // 启用自动升级到WebSocket
            rememberUpgrade: true, // 记住升级状态
            pingTimeout: 10000, // 减少ping超时
            pingInterval: 5000 // 减少ping间隔
        });
        
        // 连接成功
        socket.on('connect', function() {
            console.log('✅ Socket.IO连接成功');
            isConnecting = false;
            reconnectAttempts = 0; // 重置重连计数
            
            // 加入当前页面
            if (window.currentPage) {
                socket.emit('join_page', { page: window.currentPage });
            }
        });
        
        // 连接断开
        socket.on('disconnect', function(reason) {
            console.log('❌ Socket.IO连接断开:', reason);
            isConnecting = false;
            
            // 只在非主动断开时记录重连尝试
            if (reason !== 'io client disconnect') {
                reconnectAttempts++;
                if (reconnectAttempts <= maxReconnectAttempts) {
                    console.log(`🔄 尝试重连 (${reconnectAttempts}/${maxReconnectAttempts})`);
                }
            }
        });
        
        // 连接错误 - 减少错误日志输出
        socket.on('connect_error', function(error) {
            isConnecting = false;
            // 只在开发环境或重要错误时输出日志
            if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                console.warn('⚠️ Socket.IO连接错误:', error.message || error);
            }
        });
        
        // 重连尝试
        socket.on('reconnect_attempt', function(attemptNumber) {
            console.log(`🔄 Socket.IO重连尝试 ${attemptNumber}/${maxReconnectAttempts}`);
        });
        
        // 重连失败
        socket.on('reconnect_failed', function() {
            console.log('❌ Socket.IO重连失败，停止尝试');
            isConnecting = false;
        });
        
        // 监听页面刷新通知
        socket.on('page_refresh', function(data) {
            console.log('📡 收到页面刷新通知:', data);
            
            if (data.page === window.currentPage || data.page === 'all') {
                handlePageRefresh(data);
            }
        });
        
        // 监听实时通知
        socket.on('notification', function(data) {
            console.log('📢 收到实时通知:', data);
            showNotification(data);
        });
        
    } catch (error) {
        console.error('❌ 初始化Socket.IO失败:', error);
        isConnecting = false;
    }
}

// 设置当前页面
function setCurrentPage(page) {
    window.currentPage = page;
    
    // 如果Socket已连接，加入页面
    if (socket && socket.connected) {
        socket.emit('join_page', { page: page });
    }
}

// 处理页面刷新
function handlePageRefresh(data) {
    const { type, payload } = data;
    
    console.log('🔄 处理页面刷新:', { type, payload, currentPage: window.currentPage });
    
    // 如果currentPage为空，尝试从URL推断页面类型
    if (!window.currentPage) {
        const path = window.location.pathname;
        if (path === '/' || path === '/index') {
            window.currentPage = 'home';
        } else if (path.includes('/team')) {
            window.currentPage = 'team';
        } else if (path.includes('/paper')) {
            window.currentPage = 'papers';
        } else if (path.includes('/innovation')) {
            window.currentPage = 'innovation';
        } else if (path.includes('/dynamic') || path.includes('/activities')) {
            window.currentPage = 'dynamic';
        }
        console.log('📍 从URL推断的页面类型:', window.currentPage);
    }
    
    // 根据当前页面类型执行相应的刷新
    switch (window.currentPage) {
        case 'home':
            console.log('🏠 刷新首页数据');
            // 首页需要刷新所有数据
            if (typeof loadTeamLeaders === 'function') {
                loadTeamLeaders();
            }
            if (typeof loadTeamMembers === 'function') {
                loadTeamMembers();
            }
            if (typeof loadPapers === 'function') {
                loadPapers();
            }
            if (typeof loadInnovationProjects === 'function') {
                loadInnovationProjects();
            }
            if (typeof loadActivities === 'function') {
                loadActivities();
            }
            break;
        case 'team':
            console.log('👥 刷新团队页面数据');
            if (typeof loadTeamMembers === 'function') {
                loadTeamMembers();
            }
            break;
        case 'papers':
            console.log('📚 刷新论文页面数据');
            if (typeof loadPapers === 'function') {
                loadPapers();
            }
            break;
        case 'innovation':
            console.log('💡 刷新科创页面数据');
            if (typeof loadInnovationProjects === 'function') {
                loadInnovationProjects();
            }
            break;
        case 'dynamic':
            console.log('📢 刷新动态页面数据');
            if (typeof loadNotifications === 'function') {
                loadNotifications();
            } else {
                console.warn('⚠️ loadNotifications 函数不存在');
            }
            break;
        default:
            // 通用刷新 - 重新加载当前页面数据
            console.log('🔄 执行页面刷新 - 默认重载:', currentPage);
            location.reload();
            break;
    }
}

// 显示通知
function showNotification(data) {
    const { title, message, type = 'info' } = data;
    
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm transform transition-all duration-300 translate-x-full`;
    
    // 根据类型设置样式
    switch (type) {
        case 'success':
            notification.className += ' bg-green-500 text-white';
            break;
        case 'error':
            notification.className += ' bg-red-500 text-white';
            break;
        case 'warning':
            notification.className += ' bg-yellow-500 text-black';
            break;
        default:
            notification.className += ' bg-blue-500 text-white';
    }
    
    notification.innerHTML = `
        <div class="flex items-start">
            <div class="flex-1">
                <h4 class="font-semibold">${title || '通知'}</h4>
                <p class="text-sm mt-1">${message || ''}</p>
            </div>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-2 text-white hover:text-gray-200">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        </div>
    `;
    
    // 添加到页面
    document.body.appendChild(notification);
    
    // 显示动画
    setTimeout(() => {
        notification.classList.remove('translate-x-full');
    }, 100);
    
    // 自动隐藏
    setTimeout(() => {
        notification.classList.add('translate-x-full');
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 300);
    }, 5000);
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 延迟初始化，确保页面完全加载
    setTimeout(initSocketIO, 2000);
});

// 立即初始化（如果页面已经加载完成）
if (document.readyState === 'loading') {
    // 页面还在加载中，等待DOMContentLoaded事件
} else {
    // 页面已经加载完成，立即初始化
    setTimeout(initSocketIO, 2000);
}

// 页面卸载时清理连接
window.addEventListener('beforeunload', function() {
    if (socket) {
        socket.disconnect();
    }
});

// 页面可见性变化时处理连接
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // 页面隐藏时，可以选择断开连接或保持连接
        console.log('📱 页面隐藏');
    } else {
        // 页面显示时，确保连接正常
        console.log('📱 页面显示');
        if (socket && !socket.connected && !isConnecting) {
            setTimeout(initSocketIO, 1000);
        }
    }
}); 