/**
 * 浏览器扩展错误过滤器
 * 用于过滤和隐藏浏览器扩展导致的错误日志
 */

(function() {
    'use strict';
    
    // 保存原始的console方法
    const originalConsole = {
        error: console.error,
        warn: console.warn,
        log: console.log
    };
    
    // 扩展错误模式
    const extensionErrorPatterns = [
        /Unchecked runtime\.lastError/,
        /A listener indicated an asynchronous response/,
        /message channel closed before a response was received/,
        /Extension context invalidated/,
        /Cannot access a chrome/,
        /chrome-extension:/,
        /moz-extension:/,
        /safari-extension:/
    ];
    
    // 检查是否是扩展错误
    function isExtensionError(message) {
        if (typeof message !== 'string') {
            return false;
        }
        
        return extensionErrorPatterns.some(pattern => pattern.test(message));
    }
    
    // 过滤console.error
    console.error = function(...args) {
        const message = args[0];
        if (isExtensionError(message)) {
            // 静默处理扩展错误
            return;
        }
        originalConsole.error.apply(console, args);
    };
    
    // 过滤console.warn
    console.warn = function(...args) {
        const message = args[0];
        if (isExtensionError(message)) {
            // 静默处理扩展错误
            return;
        }
        originalConsole.warn.apply(console, args);
    };
    
    // 过滤console.log（可选）
    console.log = function(...args) {
        const message = args[0];
        if (isExtensionError(message)) {
            // 静默处理扩展错误
            return;
        }
        originalConsole.log.apply(console, args);
    };
    
    // 监听未捕获的错误
    window.addEventListener('error', function(event) {
        if (isExtensionError(event.message)) {
            event.preventDefault();
            return false;
        }
    });
    
    // 监听未处理的Promise拒绝
    window.addEventListener('unhandledrejection', function(event) {
        if (isExtensionError(event.reason)) {
            event.preventDefault();
            return false;
        }
    });
    
    console.log('🔧 浏览器扩展错误过滤器已启用');
})(); 