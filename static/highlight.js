// Simple highlight.js placeholder
document.addEventListener('DOMContentLoaded', function() {
    // 查找所有需要高亮的代码块
    const codeBlocks = document.querySelectorAll('pre code');
    
    codeBlocks.forEach(function(block) {
        // 简单的高亮处理（可以在需要时扩展）
        if (!block.classList.contains('hljs')) {
            block.classList.add('hljs');
        }
    });
    
    console.log('代码高亮已加载');
}); 