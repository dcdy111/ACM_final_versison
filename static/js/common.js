/**
 * ACM实验室网站通用JavaScript函数
 * 提供前端页面需要的基础功能
 */

// 全局变量
let currentPage = '';

// 设置当前页面
function setCurrentPage(page) {
    currentPage = page;
    console.log('设置当前页面:', page);
    
    // 如果Socket已连接，加入页面
    if (typeof socket !== 'undefined' && socket && socket.connected) {
        socket.emit('join_page', { page: page });
    }
}

// 显示通知提示
function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        z-index: 99999;
        transition: all 0.3s ease;
        transform: translateX(100%);
        max-width: 400px;
        word-wrap: break-word;
        font-size: 14px;
        font-weight: 500;
    `;
    
    // 根据类型设置样式
    if (type === 'success') {
        notification.style.backgroundColor = '#10b981';
        notification.style.color = '#ffffff';
        notification.style.border = '1px solid #059669';
        notification.innerHTML = `<i class="fa fa-check-circle" style="margin-right: 8px;"></i>${message}`;
    } else if (type === 'error') {
        notification.style.backgroundColor = '#ef4444';
        notification.style.color = '#ffffff';
        notification.style.border = '1px solid #dc2626';
        notification.innerHTML = `<i class="fa fa-exclamation-circle" style="margin-right: 8px;"></i>${message}`;
    } else {
        notification.style.backgroundColor = '#3b82f6';
        notification.style.color = '#ffffff';
        notification.style.border = '1px solid #2563eb';
        notification.innerHTML = `<i class="fa fa-info-circle" style="margin-right: 8px;"></i>${message}`;
    }
    
    document.body.appendChild(notification);
    
    // 动画显示
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // 3秒后自动消失
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 节流函数
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// 格式化日期
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// 格式化数字
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

// 检查元素是否在视口中
function isElementInViewport(el) {
    const rect = el.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

// 懒加载图片
function lazyLoadImages() {
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                imageObserver.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

// 页面加载完成后的通用初始化
function initCommonFeatures() {
    // 懒加载图片
    lazyLoadImages();
    
    // 平滑滚动
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // 返回顶部按钮（已隐藏）
    /*
    const backToTopBtn = document.createElement('button');
    backToTopBtn.innerHTML = '<i class="fa fa-arrow-up"></i>';
    backToTopBtn.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: rgba(58, 134, 255, 0.8);
        color: white;
        border: none;
        cursor: pointer;
        opacity: 0;
        transition: all 0.3s ease;
        z-index: 1000;
        backdrop-filter: blur(10px);
    `;
    
    backToTopBtn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
    
    document.body.appendChild(backToTopBtn);
    
    // 滚动时显示/隐藏返回顶部按钮
    window.addEventListener('scroll', throttle(() => {
        if (window.pageYOffset > 300) {
            backToTopBtn.style.opacity = '1';
        } else {
            backToTopBtn.style.opacity = '0';
        }
    }, 100));
    */
}

// 导出到全局
window.setCurrentPage = setCurrentPage;
window.showNotification = showNotification;
window.debounce = debounce;
window.throttle = throttle;
window.formatDate = formatDate;
window.formatNumber = formatNumber;
window.initCommonFeatures = initCommonFeatures;

// 页面加载完成后自动初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCommonFeatures);
} else {
    initCommonFeatures();
} 