/**
 * 错误处理配置文件
 * 统一管理错误处理策略和配置
 */

window.ErrorConfig = {
    // 错误处理级别
    levels: {
        DEBUG: 0,
        INFO: 1,
        WARN: 2,
        ERROR: 3,
        CRITICAL: 4
    },
    
    // 当前错误处理级别
    currentLevel: 2, // WARN级别
    
    // 错误分类配置
    categories: {
        // 网络错误
        network: {
            patterns: [
                /Failed to fetch/,
                /NetworkError/,
                /ERR_NETWORK/,
                /ERR_INTERNET_DISCONNECTED/,
                /ERR_CONNECTION_REFUSED/,
                /ERR_CONNECTION_TIMED_OUT/
            ],
            level: 3, // ERROR
            retry: true,
            maxRetries: 3
        },
        
        // 浏览器扩展错误
        extension: {
            patterns: [
                /Unchecked runtime\.lastError/,
                /Extension context invalidated/,
                /chrome-extension:/,
                /moz-extension:/,
                /safari-extension:/
            ],
            level: 1, // INFO (静默处理)
            retry: false
        },
        
        // 用户操作错误
        user: {
            patterns: [
                /User cancelled/,
                /Permission denied/,
                /Access denied/
            ],
            level: 2, // WARN
            retry: false
        },
        
        // 系统错误
        system: {
            patterns: [
                /Internal server error/,
                /500/,
                /502/,
                /503/,
                /504/
            ],
            level: 4, // CRITICAL
            retry: true,
            maxRetries: 5
        },
        
        // 数据错误
        data: {
            patterns: [
                /Invalid JSON/,
                /Unexpected token/,
                /SyntaxError/,
                /TypeError/
            ],
            level: 3, // ERROR
            retry: false
        }
    },
    
    // 错误处理策略
    strategies: {
        // 静默处理
        silent: (error, context) => {
            // 不显示任何错误信息
            return false;
        },
        
        // 用户友好提示
        userFriendly: (error, context) => {
            const message = getErrorMessage(error, context);
            showMessage(message, 'error');
            return true;
        },
        
        // 详细错误信息
        detailed: (error, context) => {
            console.error('详细错误信息:', error);
            const message = getErrorMessage(error, context);
            showMessage(message, 'error');
            return true;
        },
        
        // 重试策略
        retry: (error, context, retryFn) => {
            const category = getErrorCategory(error);
            const config = ErrorConfig.categories[category];
            
            if (config && config.retry && context.retryCount < config.maxRetries) {
                context.retryCount = (context.retryCount || 0) + 1;
                setTimeout(() => {
                    retryFn();
                }, 1000 * context.retryCount); // 递增延迟
                return true;
            }
            return false;
        }
    },
    
    // 获取错误分类
    getErrorCategory: function(error) {
        const message = error.message || error.toString();
        
        for (const [category, config] of Object.entries(this.categories)) {
            if (config.patterns.some(pattern => pattern.test(message))) {
                return category;
            }
        }
        
        return 'unknown';
    },
    
    // 获取错误处理级别
    getErrorLevel: function(error) {
        const category = this.getErrorCategory(error);
        const config = this.categories[category];
        return config ? config.level : this.levels.ERROR;
    },
    
    // 检查是否应该处理错误
    shouldHandleError: function(error) {
        const level = this.getErrorLevel(error);
        return level >= this.currentLevel;
    },
    
    // 获取用户友好的错误消息
    getErrorMessage: function(error, context) {
        const category = this.getErrorCategory(error);
        const message = error.message || error.toString();
        
        const errorMessages = {
            network: {
                'Failed to fetch': '网络连接失败，请检查网络设置',
                'NetworkError': '网络错误，请稍后重试',
                'ERR_NETWORK': '网络连接异常',
                'ERR_INTERNET_DISCONNECTED': '网络连接已断开',
                'ERR_CONNECTION_REFUSED': '连接被拒绝',
                'ERR_CONNECTION_TIMED_OUT': '连接超时'
            },
            system: {
                'Internal server error': '服务器内部错误',
                '500': '服务器错误，请稍后重试',
                '502': '网关错误',
                '503': '服务暂时不可用',
                '504': '网关超时'
            },
            data: {
                'Invalid JSON': '数据格式错误',
                'Unexpected token': '数据解析失败',
                'SyntaxError': '语法错误',
                'TypeError': '类型错误'
            },
            user: {
                'User cancelled': '操作已取消',
                'Permission denied': '权限不足',
                'Access denied': '访问被拒绝'
            }
        };
        
        const categoryMessages = errorMessages[category];
        if (categoryMessages) {
            for (const [pattern, friendlyMessage] of Object.entries(categoryMessages)) {
                if (message.includes(pattern)) {
                    return friendlyMessage;
                }
            }
        }
        
        // 默认错误消息
        return context?.userMessage || '操作失败，请稍后重试';
    }
};

// 导出配置
if (typeof module !== 'undefined' && module.exports) {
    module.exports = window.ErrorConfig;
} 