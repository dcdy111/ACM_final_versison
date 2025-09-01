// 性能监控器
class PerformanceMonitor {
    constructor() {
        this.metrics = {};
        this.init();
    }

    init() {
        this.measurePageLoad();
        this.measureResourceLoading();
        this.logPerformanceMetrics();
    }

    measurePageLoad() {
        window.addEventListener('load', () => {
            const navigation = performance.getEntriesByType('navigation')[0];
            if (navigation) {
                this.metrics.pageLoad = {
                    domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                    loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
                    totalTime: navigation.loadEventEnd - navigation.fetchStart,
                    dnsLookup: navigation.domainLookupEnd - navigation.domainLookupStart,
                    tcpConnection: navigation.connectEnd - navigation.connectStart,
                    serverResponse: navigation.responseEnd - navigation.responseStart
                };
            }
        });
    }

    measureResourceLoading() {
        // 监控资源加载
        const observer = new PerformanceObserver((list) => {
            list.getEntries().forEach((entry) => {
                if (entry.entryType === 'resource') {
                    if (!this.metrics.resources) {
                        this.metrics.resources = [];
                    }
                    this.metrics.resources.push({
                        name: entry.name,
                        duration: entry.duration,
                        size: entry.transferSize || 0,
                        type: this.getResourceType(entry.name)
                    });
                }
            });
        });
        
        observer.observe({ entryTypes: ['resource'] });
    }

    getResourceType(url) {
        if (url.includes('.css')) return 'CSS';
        if (url.includes('.js')) return 'JavaScript';
        if (url.includes('.png') || url.includes('.jpg') || url.includes('.jpeg') || url.includes('.gif')) return 'Image';
        if (url.includes('.woff') || url.includes('.ttf')) return 'Font';
        return 'Other';
    }

    logPerformanceMetrics() {
        setTimeout(() => {
            console.group('🚀 页面性能报告');
            
            if (this.metrics.pageLoad) {
                console.log('📊 页面加载时间:');
                console.log(`  • DOM准备完成: ${this.metrics.pageLoad.domContentLoaded.toFixed(2)}ms`);
                console.log(`  • 页面完全加载: ${this.metrics.pageLoad.totalTime.toFixed(2)}ms`);
                console.log(`  • DNS查询: ${this.metrics.pageLoad.dnsLookup.toFixed(2)}ms`);
                console.log(`  • 服务器响应: ${this.metrics.pageLoad.serverResponse.toFixed(2)}ms`);
            }

            if (this.metrics.resources) {
                console.log('\n📦 资源加载统计:');
                const resourceStats = this.analyzeResources();
                Object.entries(resourceStats).forEach(([type, stats]) => {
                    console.log(`  • ${type}: ${stats.count}个文件, 总计${(stats.totalSize/1024).toFixed(2)}KB, 平均${stats.avgDuration.toFixed(2)}ms`);
                });
            }

            // 提供性能建议
            this.provideOptimizationSuggestions();
            
            console.groupEnd();
        }, 3000);
    }

    analyzeResources() {
        const stats = {};
        this.metrics.resources.forEach(resource => {
            if (!stats[resource.type]) {
                stats[resource.type] = {
                    count: 0,
                    totalSize: 0,
                    totalDuration: 0
                };
            }
            stats[resource.type].count++;
            stats[resource.type].totalSize += resource.size;
            stats[resource.type].totalDuration += resource.duration;
        });

        // 计算平均值
        Object.values(stats).forEach(stat => {
            stat.avgDuration = stat.totalDuration / stat.count;
        });

        return stats;
    }

    provideOptimizationSuggestions() {
        console.log('\n💡 性能优化建议:');
        
        if (this.metrics.pageLoad && this.metrics.pageLoad.totalTime > 3000) {
            console.log('  ⚠️ 页面加载时间较长，建议优化图片和资源');
        } else {
            console.log('  ✅ 页面加载时间良好');
        }

        if (this.metrics.resources) {
            const imageResources = this.metrics.resources.filter(r => r.type === 'Image');
            const totalImageSize = imageResources.reduce((sum, img) => sum + img.size, 0);
            
            if (totalImageSize > 500 * 1024) { // 500KB
                console.log('  ⚠️ 图片总大小较大，建议压缩或使用懒加载');
            }

            const jsResources = this.metrics.resources.filter(r => r.type === 'JavaScript');
            if (jsResources.length > 10) {
                console.log('  ⚠️ JavaScript文件较多，建议合并或延迟加载');
            }
        }
    }

    // 获取核心Web指标
    getCoreWebVitals() {
        return new Promise((resolve) => {
            const vitals = {};
            
            // Largest Contentful Paint (LCP)
            new PerformanceObserver((list) => {
                const entries = list.getEntries();
                const lastEntry = entries[entries.length - 1];
                vitals.lcp = lastEntry.startTime;
            }).observe({ entryTypes: ['largest-contentful-paint'] });

            // First Input Delay (FID) 和 Cumulative Layout Shift (CLS)
            // 需要用户交互才能测量
            
            setTimeout(() => resolve(vitals), 5000);
        });
    }
}

// 在开发环境下启用性能监控
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    new PerformanceMonitor();
} 