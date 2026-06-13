(function () {
    const isMobile = () => window.innerWidth <= 992;

    function wrapTables() {
        if (!isMobile()) return;
        document.querySelectorAll('.content-block table').forEach(function (table) {
            if (table.closest('.table-responsive, .mobile-table-wrap')) return;
            const wrapper = document.createElement('div');
            wrapper.className = 'mobile-table-wrap';
            table.parentNode.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        });
    }

    function closeSidebarAfterNavigate() {
        const sidebar = document.getElementById('appSidebar');
        const overlay = document.getElementById('mobileOverlay');
        if (!sidebar) return;
        sidebar.querySelectorAll('a').forEach(function (link) {
            link.addEventListener('click', function () {
                if (!isMobile()) return;
                sidebar.classList.remove('mobile-open');
                if (overlay) overlay.classList.remove('show');
            });
        });
    }

    function keepFocusedFieldVisible() {
        if (!isMobile()) return;
        document.querySelectorAll('input, select, textarea').forEach(function (field) {
            field.addEventListener('focus', function () {
                setTimeout(function () {
                    try {
                        field.scrollIntoView({ block: 'center', behavior: 'smooth' });
                    } catch (err) {}
                }, 250);
            });
        });
    }

    function markBodyMode() {
        document.body.classList.toggle('bys-mobile-active', isMobile());
    }

    document.addEventListener('DOMContentLoaded', function () {
        markBodyMode();
        wrapTables();
        closeSidebarAfterNavigate();
        keepFocusedFieldVisible();
    });

    window.addEventListener('resize', function () {
        markBodyMode();
        wrapTables();
    });
})();
