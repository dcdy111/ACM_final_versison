// 性能优化加载器
class PerformanceLoader {
    constructor() {
        this.loadedResources = new Set();
        this.init();
    }

    init() {
        // 预加载关键资源
        this.preloadCriticalResources();
        
        // DOM加载完成后初始化
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.optimize());
        } else {
            this.optimize();
        }
    }

    optimize() {
        // 延迟加载非关键资源
        this.lazyLoadFonts();
        this.lazyLoadIcons();
        this.lazyLoadSocketIO();
        this.optimizeImages();
        this.enablePrefetch();
        this.optimizeScroll();
    }

    lazyLoadFonts() {
        // 如果字体还未加载，延迟加载
        setTimeout(() => {
            if (!this.loadedResources.has('fonts')) {
                const fontLink = document.createElement('link');
                fontLink.href = 'https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Exo+2:wght@300;500&display=swap';
                fontLink.rel = 'stylesheet';
                document.head.appendChild(fontLink);
                this.loadedResources.add('fonts');
            }
        }, 100);
    }

    lazyLoadIcons() {
        // 延迟加载图标字体
        setTimeout(() => {
            if (!this.loadedResources.has('icons')) {
                const iconLink1 = document.createElement('link');
                iconLink1.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css';
                iconLink1.rel = 'stylesheet';
                document.head.appendChild(iconLink1);

                const iconLink2 = document.createElement('link');
                iconLink2.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/v4-shims.min.css';
                iconLink2.rel = 'stylesheet';
                document.head.appendChild(iconLink2);
                
                this.loadedResources.add('icons');
            }
        }, 500);
    }

    lazyLoadSocketIO() {
        // 延迟加载Socket.IO (仅在需要时)
        setTimeout(() => {
            if (!this.loadedResources.has('socketio') && !window.io) {
                const socketScript = document.createElement('script');
                socketScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.js';
                socketScript.onload = () => {
                    const clientScript = document.createElement('script');
                    clientScript.src = '/static/socket-client.js';
                    document.head.appendChild(clientScript);
                };
                document.head.appendChild(socketScript);
                this.loadedResources.add('socketio');
            }
        }, 2000);
    }

    optimizeImages() {
        // 图片懒加载
        const images = document.querySelectorAll('img[data-src]');
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    observer.unobserve(img);
                }
            });
        });

        images.forEach(img => imageObserver.observe(img));
    }

    // 预加载关键资源
    preloadCriticalResources() {
        const criticalResources = [
            { href: '/static/highlight.css', as: 'style' },
            { href: 'https://cdn.tailwindcss.com', as: 'script' }
        ];

        criticalResources.forEach(resource => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.href = resource.href;
            link.as = resource.as;
            document.head.appendChild(link);
        });
    }

    // 启用页面预加载
    enablePrefetch() {
        // 预加载导航链接
        const navLinks = document.querySelectorAll('nav a[href^="/"]');
        navLinks.forEach(link => {
            link.addEventListener('mouseenter', () => {
                if (!this.loadedResources.has(link.href)) {
                    const prefetchLink = document.createElement('link');
                    prefetchLink.rel = 'prefetch';
                    prefetchLink.href = link.href;
                    document.head.appendChild(prefetchLink);
                    this.loadedResources.add(link.href);
                }
            });
        });
    }

    // 滚动性能优化
    optimizeScroll() {
        let ticking = false;
        const handleScroll = () => {
            if (!ticking) {
                requestAnimationFrame(() => {
                    // 在这里处理滚动事件
                    ticking = false;
                });
                ticking = true;
            }
        };
        
        // 使用被动监听器
        window.addEventListener('scroll', handleScroll, { passive: true });
    }
}

// 自动初始化
new PerformanceLoader(); 