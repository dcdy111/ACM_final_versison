(function() {
	document.addEventListener('DOMContentLoaded', function() {
		const currentPage = decodeURIComponent(window.location.pathname.split('/').pop() || 'index.html');
		const pageMapping = {
			'index.html': { navSelector: '.logo', footerText: 'ACM实验室' },
			'Introduction to the Laboratory.html': { navText: '实验室概况', dropdownText: '实验室简介', footerText: '实验室简介' },
			'Laboratory Charter.html': { navText: '实验室概况', dropdownText: '实验室章程', footerText: '实验室章程' },
			'team.html': { navText: '团队', footerText: '团队' },
			'paper.html': { navText: '成果性展示', dropdownText: '论文', footerText: '论文' },
			'algorithm.html': { navText: '成果性展示', dropdownText: '算法', footerText: '算法' },
			'science and technology innovation.html': { navText: '成果性展示', dropdownText: '科创', footerText: '科创' },
			'enterprise.html': { navText: '成果性展示', dropdownText: '企业', footerText: '企业' },
			'dynamic.html': { navText: '动态', footerText: '动态' },
			'Recruitment for the Algorithm Group.html': { navText: '加入我们', dropdownText: '算法组招生', footerText: '算法组招生' },
			'Project team recruitment.html': { navText: '加入我们', dropdownText: '项目组招生', footerText: '项目组招生' }
		};

		const info = pageMapping[currentPage];
		if (!info) return;

		if (info.navSelector) {
			const el = document.querySelector(info.navSelector);
			if (el) el.classList.add('active');
		} else if (info.navText) {
			const navLinks = document.querySelectorAll('.nav-link');
			navLinks.forEach(link => {
				if (link.textContent.trim() === info.navText) link.classList.add('active');
			});
			if (info.dropdownText) {
				const dropdownLinks = document.querySelectorAll('.dropdown-link');
				dropdownLinks.forEach(link => {
					if (link.textContent.trim() === info.dropdownText) link.classList.add('active');
				});
			}
		}

		if (info.footerText) {
			const footerLinks = document.querySelectorAll('.footer-link');
			footerLinks.forEach(link => {
				if (link.textContent.trim() === info.footerText) link.classList.add('active');
			});
		}

		if (currentPage === 'index.html') {
			const footerLogo = document.querySelector('.footer-logo');
			if (footerLogo) footerLogo.classList.add('active');
		}
	});
})(); 