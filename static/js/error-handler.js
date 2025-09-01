/**
 * 统一错误处理工具
 * 提供智能错误分类、用户友好提示和自动重试功能
 */

window.ErrorHandler = {
    // 错误处理配置
    config: window.ErrorConfig || {
        currentLevel: 2,
        shouldHandleError: () => true,
        getErrorMessage: (error, context) => context?.userMessage || '操作失败，请稍后重试'
    },
    
    // 处理网络错误
    handleNetworkError: function(error, context, showMessageFn) {
        if (!this.config.shouldHandleError(error)) {
            return false;
        }
        
        const message = this.config.getErrorMessage(error, { 
            ...context, 
            userMessage: '网络连接失败，请检查网络设置后重试' 
        });
        
        if (showMessageFn && typeof showMessageFn === 'function') {
            showMessageFn(message, 'error');
        } else {
            this.showDefaultMessage(message, 'error');
        }
        
        return true;
    },
    
    // 处理数据错误
    handleDataError: function(error, context, showMessageFn) {
        if (!this.config.shouldHandleError(error)) {
            return false;
        }
        
        const message = this.config.getErrorMessage(error, { 
            ...context, 
            userMessage: '数据格式错误，请刷新页面重试' 
        });
        
        if (showMessageFn && typeof showMessageFn === 'function') {
            showMessageFn(message, 'error');
        } else {
            this.showDefaultMessage(message, 'error');
        }
        
        return true;
    },
    
    // 处理权限错误
    handlePermissionError: function(error, context, showMessageFn) {
        if (!this.config.shouldHandleError(error)) {
            return false;
        }
        
        const message = this.config.getErrorMessage(error, { 
            ...context, 
            userMessage: '权限不足，请检查登录状态' 
        });
        
        if (showMessageFn && typeof showMessageFn === 'function') {
            showMessageFn(message, 'warning');
        } else {
            this.showDefaultMessage(message, 'warning');
        }
        
        return true;
    },
    
    // 处理系统错误
    handleSystemError: function(error, context, showMessageFn) {
        if (!this.config.shouldHandleError(error)) {
            return false;
        }
        
        const message = this.config.getErrorMessage(error, { 
            ...context, 
            userMessage: '系统错误，请稍后重试' 
        });
        
        if (showMessageFn && typeof showMessageFn === 'function') {
            showMessageFn(message, 'error');
        } else {
            this.showDefaultMessage(message, 'error');
        }
        
        return true;
    },
    
    // 处理用户操作错误
    handleUserError: function(error, context, showMessageFn) {
        if (!this.config.shouldHandleError(error)) {
            return false;
        }
        
        const message = this.config.getErrorMessage(error, { 
            ...context, 
            userMessage: '操作失败，请重试' 
        });
        
        if (showMessageFn && typeof showMessageFn === 'function') {
            showMessageFn(message, 'info');
        } else {
            this.showDefaultMessage(message, 'info');
        }
        
        return true;
    },
    
    // 智能错误处理
    handleError: function(error, context, showMessageFn) {
        const errorMessage = error.message || error.toString();
        
        // 根据错误类型选择处理策略
        if (this.isNetworkError(errorMessage)) {
            return this.handleNetworkError(error, context, showMessageFn);
        } else if (this.isDataError(errorMessage)) {
            return this.handleDataError(error, context, showMessageFn);
        } else if (this.isPermissionError(errorMessage)) {
            return this.handlePermissionError(error, context, showMessageFn);
        } else if (this.isSystemError(errorMessage)) {
            return this.handleSystemError(error, context, showMessageFn);
        } else if (this.isUserError(errorMessage)) {
            return this.handleUserError(error, context, showMessageFn);
        } else {
            // 默认处理
            const message = this.config.getErrorMessage(error, context);
            if (showMessageFn && typeof showMessageFn === 'function') {
                showMessageFn(message, 'error');
            } else {
                this.showDefaultMessage(message, 'error');
            }
            return true;
        }
    },
    
    // 错误类型检测
    isNetworkError: function(message) {
        const patterns = [
            /Failed to fetch/,
            /NetworkError/,
            /ERR_NETWORK/,
            /ERR_INTERNET_DISCONNECTED/,
            /ERR_CONNECTION_REFUSED/,
            /ERR_CONNECTION_TIMED_OUT/
        ];
        return patterns.some(pattern => pattern.test(message));
    },
    
    isDataError: function(message) {
        const patterns = [
            /Invalid JSON/,
            /Unexpected token/,
            /SyntaxError/,
            /TypeError/
        ];
        return patterns.some(pattern => pattern.test(message));
    },
    
    isPermissionError: function(message) {
        const patterns = [
            /Permission denied/,
            /Access denied/,
            /401/,
            /403/
        ];
        return patterns.some(pattern => pattern.test(message));
    },
    
    isSystemError: function(message) {
        const patterns = [
            /Internal server error/,
            /500/,
            /502/,
            /503/,
            /504/
        ];
        return patterns.some(pattern => pattern.test(message));
    },
    
    isUserError: function(message) {
        const patterns = [
            /User cancelled/,
            /Validation failed/,
            /Invalid input/
        ];
        return patterns.some(pattern => pattern.test(message));
    },
    
    // 默认消息显示
    showDefaultMessage: function(message, type) {
        // 创建消息元素
        const messageEl = document.createElement('div');
        messageEl.className = `error-message ${type}`;
        messageEl.textContent = message;
        
        // 样式
        messageEl.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 6px;
            color: white;
            font-size: 14px;
            z-index: 10000;
            max-width: 300px;
            word-wrap: break-word;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: slideIn 0.3s ease-out;
        `;
        
        // 根据类型设置背景色
        const colors = {
            error: '#f56565',
            warning: '#ed8936',
            info: '#3182ce',
            success: '#38a169'
        };
        messageEl.style.backgroundColor = colors[type] || colors.error;
        
        // 添加到页面
        document.body.appendChild(messageEl);
        
        // 3秒后自动移除
        setTimeout(() => {
            messageEl.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => {
                if (messageEl.parentNode) {
                    messageEl.parentNode.removeChild(messageEl);
                }
            }, 300);
        }, 3000);
    },
    
    // 带重试的错误处理
    handleWithRetry: function(error, context, retryFn, maxRetries = 3) {
        if (!context.retryCount) {
            context.retryCount = 0;
        }
        
        if (context.retryCount < maxRetries && this.isRetryableError(error)) {
            context.retryCount++;
            const delay = 1000 * context.retryCount; // 递增延迟
            
            setTimeout(() => {
                retryFn();
            }, delay);
            
            return true;
        }
        
        // 重试次数用完，显示错误
        return this.handleError(error, context);
    },
    
    // 判断是否可重试的错误
    isRetryableError: function(error) {
        const message = error.message || error.toString();
        return this.isNetworkError(message) || this.isSystemError(message);
    }
};

// 添加CSS动画
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

console.log('🔧 智能错误处理工具已加载'); 