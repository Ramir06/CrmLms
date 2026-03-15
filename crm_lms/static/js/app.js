/* ===== CRM LMS — Global App JS ===== */

document.addEventListener('DOMContentLoaded', function () {

    // ── Sidebar toggle ──────────────────────────────────────────────────────
    const sidebar = document.getElementById('appSidebar');
    const contentOverlay = document.getElementById('contentOverlay');

    function openSidebar() {
        if (!sidebar) return;
        sidebar.classList.add('menu-open');
        if (contentOverlay) contentOverlay.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        if (!sidebar) return;
        sidebar.classList.remove('menu-open');
        if (contentOverlay) contentOverlay.classList.remove('show');
        document.body.style.overflow = '';
    }

    // Mobile hamburger toggle (in navbar)
    const mobileToggleBtn = document.getElementById('sidebarToggle');
    if (mobileToggleBtn) {
        mobileToggleBtn.addEventListener('click', function () {
            if (sidebar && sidebar.classList.contains('menu-open')) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });
    }

    // Sidebar close button (inside sidebar header)
    const collapseBtn = document.getElementById('sidebarCollapseBtn');
    if (collapseBtn) {
        collapseBtn.addEventListener('click', closeSidebar);
    }

    // Content overlay click closes sidebar
    if (contentOverlay) {
        contentOverlay.addEventListener('click', closeSidebar);
    }

    // ── Theme toggle ────────────────────────────────────────────────────────
    const themeBtn = document.getElementById('themeToggle') ||
                     document.querySelector('[data-action="theme-toggle"]');
    const htmlEl = document.documentElement;
    const savedTheme = localStorage.getItem('theme') || 'light';
    
    // Apply theme on load
    applyTheme(savedTheme);
    
    if (themeBtn) {
        themeBtn.addEventListener('click', function () {
            const current = localStorage.getItem('theme') || 'light';
            const next = current === 'dark' ? 'light' : 'dark';
            applyTheme(next);
            localStorage.setItem('theme', next);
        });
    }

    function applyTheme(theme) {
        if (theme === 'dark') {
            htmlEl.classList.add('dark-layout');
            htmlEl.setAttribute('data-bs-theme', 'dark');
        } else {
            htmlEl.classList.remove('dark-layout');
            htmlEl.setAttribute('data-bs-theme', 'light');
        }
        updateThemeIcon(themeBtn, theme);
    }

    function updateThemeIcon(btn, theme) {
        if (!btn) return;
        const icon = btn.querySelector('i') || document.getElementById('themeIcon');
        if (!icon) return;
        icon.className = theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon';
    }

    // ── Auto-dismiss messages ───────────────────────────────────────────────
    document.querySelectorAll('.alert.alert-dismissible').forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000);
    });

    // ── Active sidebar link highlight (handled server-side via Django template tags) ──

    // ── Drawer helpers ──────────────────────────────────────────────────────
    window.openDrawer = function (title, content) {
        const drawer = document.getElementById('drawerPanel') ||
                       document.getElementById('lessonDrawer');
        const overlay = document.getElementById('drawerOverlay');
        const drawerTitle = document.getElementById('drawerTitle');
        const drawerBody = document.getElementById('drawerBody');

        if (!drawer) return;
        if (title && drawerTitle) drawerTitle.textContent = title;
        if (content && drawerBody) drawerBody.innerHTML = content;

        drawer.classList.add('open');
        if (overlay) overlay.classList.add('show');
        document.body.style.overflow = 'hidden';
    };

    window.closeDrawer = function () {
        const drawer = document.getElementById('drawerPanel') ||
                       document.getElementById('lessonDrawer');
        const overlay = document.getElementById('drawerOverlay');
        if (drawer) drawer.classList.remove('open');
        if (overlay) overlay.classList.remove('show');
        document.body.style.overflow = '';
    };

    // Close drawer on overlay click
    document.getElementById('drawerOverlay')?.addEventListener('click', window.closeDrawer);

    // ── Confirm delete forms ────────────────────────────────────────────────
    document.querySelectorAll('form[data-confirm]').forEach(function (form) {
        form.addEventListener('submit', function (e) {
            if (!confirm(form.dataset.confirm || 'Удалить?')) {
                e.preventDefault();
            }
        });
    });

    // ── Initialize Bootstrap tooltips ───────────────────────────────────────
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
        new bootstrap.Tooltip(el);
    });

});
