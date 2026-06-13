(function () {
    function isMobile() {
        return window.innerWidth <= 992;
    }

    function syncSidebarState() {
        const sidebar = document.getElementById('appSidebar');
        const overlay = document.getElementById('mobileOverlay');
        const open = !!(sidebar && sidebar.classList.contains('mobile-open') && isMobile());
        document.body.classList.toggle('sidebar-mobile-locked', open);
        if (overlay) {
            overlay.classList.toggle('show', open);
        }
    }

    function closeSidebar() {
        const sidebar = document.getElementById('appSidebar');
        if (sidebar) {
            sidebar.classList.remove('mobile-open');
        }
        syncSidebarState();
    }

    function bindSidebarLifecycle() {
        const toggle = document.getElementById('menuToggle');
        const overlay = document.getElementById('mobileOverlay');
        const sidebar = document.getElementById('appSidebar');
        if (!sidebar) return;

        if (toggle) {
            toggle.addEventListener('click', function () {
                window.setTimeout(syncSidebarState, 10);
            });
        }

        if (overlay) {
            overlay.addEventListener('click', function () {
                closeSidebar();
            });
        }

        sidebar.querySelectorAll('a[href]').forEach(function (link) {
            link.addEventListener('click', function () {
                if (!isMobile()) return;
                closeSidebar();
            });
        });
    }

    function keepFocusedFieldVisible() {
        if (!isMobile()) return;
        document.querySelectorAll('input, select, textarea').forEach(function (field) {
            field.addEventListener('focus', function () {
                window.setTimeout(function () {
                    try {
                        field.scrollIntoView({ block: 'center', behavior: 'smooth' });
                    } catch (err) {}
                }, 220);
            });
        });
    }

    function bindResize() {
        window.addEventListener('resize', function () {
            if (!isMobile()) {
                document.body.classList.remove('sidebar-mobile-locked');
            }
            syncSidebarState();
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        bindSidebarLifecycle();
        keepFocusedFieldVisible();
        syncSidebarState();
        bindResize();
    });
})();
