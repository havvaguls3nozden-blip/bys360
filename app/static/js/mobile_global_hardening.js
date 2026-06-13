(function () {
    const BREAKPOINT = 992;
    const SCOPE = 'main, .content-wrap, .content-block, .container, .container-fluid, .login-shell, .reset-shell, .shell, .error-shell, .bys-about, body';
    const EXCLUDE = '.app-sidebar, .topbar, .mobile-dock, .dropdown-menu, .user-dropdown, .modal, .modal-dialog, .toast, .tox, .note-editor, .fc, .CodeMirror, .skip-mobile-normalize';

    function isMobile() {
        return window.innerWidth <= BREAKPOINT;
    }

    function inScope(el) {
        return !!el.closest(SCOPE);
    }

    function shouldSkip(el) {
        return !el || !inScope(el) || !!el.closest(EXCLUDE);
    }

    function wrapTables() {
        if (!isMobile()) return;
        document.querySelectorAll('table').forEach(function (table) {
            if (table.closest('.table-responsive, .mobile-table-wrap, .skip-mobile-wrap, .note-editor, .tox, .fc, .CodeMirror')) return;
            const wrapper = document.createElement('div');
            wrapper.className = 'mobile-table-wrap';
            table.parentNode.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        });
    }

    function normalizeInlineWidths() {
        if (!isMobile()) return;
        const limit = Math.max(460, window.innerWidth - 32);
        document.querySelectorAll('[style]').forEach(function (el) {
            if (shouldSkip(el)) return;
            if (/^(TABLE|THEAD|TBODY|TR|TD|TH|IMG|SVG|CANVAS|VIDEO|IFRAME)$/.test(el.tagName)) return;
            const styleText = (el.getAttribute('style') || '').toLowerCase();
            const widths = Array.from(styleText.matchAll(/(?:min-width|width|max-width)\s*:\s*([0-9]+)px/g)).map(function (m) {
                return parseInt(m[1], 10);
            });
            if (widths.some(function (v) { return v > limit; })) {
                el.classList.add('mobile-fullwidth', 'mobile-trim-minwidth', 'mobile-wrap-text');
            }
            if (styleText.includes('white-space:nowrap') || styleText.includes('white-space: nowrap')) {
                el.classList.add('mobile-wrap-text');
            }
            if (styleText.includes('grid-template-columns')) {
                el.classList.add('mobile-force-stack', 'mobile-fullwidth', 'mobile-trim-minwidth');
            }
        });
    }

    function normalizeComputedLayouts() {
        if (!isMobile()) return;
        document.querySelectorAll('body *').forEach(function (el) {
            if (shouldSkip(el)) return;
            const tag = el.tagName;
            if (/^(TABLE|THEAD|TBODY|TR|TD|TH|SCRIPT|STYLE|LINK)$/.test(tag)) return;
            const css = window.getComputedStyle(el);
            const name = ((el.className && el.className.toString()) || '').toLowerCase();

            if (css.display === 'grid') {
                const cols = (css.gridTemplateColumns || '').split(' ').filter(Boolean);
                if (cols.length > 1) {
                    if (!name.includes('mobile-dock')) {
                        el.classList.add('mobile-force-stack', 'mobile-fullwidth', 'mobile-trim-minwidth');
                    }
                }
            }

            if (css.display === 'flex' && css.flexWrap === 'nowrap') {
                if (el.scrollWidth > el.clientWidth + 12 && /(action|filter|toolbar|header|top|meta|control|row|group|tabs|list|summary)/.test(name)) {
                    el.classList.add('mobile-flex-wrap');
                }
            }

            if (css.whiteSpace === 'nowrap' && el.scrollWidth > el.clientWidth + 20) {
                if (!/(badge|pill|count|icon|avatar|btn|nav-link|quick-link)/.test(name)) {
                    el.classList.add('mobile-wrap-text');
                }
            }

            if (['DIV', 'SECTION', 'ARTICLE', 'FORM', 'ASIDE'].includes(tag) && el.scrollWidth > el.clientWidth + 24 && !el.querySelector('table')) {
                el.classList.add('mobile-fullwidth', 'mobile-trim-minwidth');
            }
        });
    }

    function normalizeMedia() {
        if (!isMobile()) return;
        document.querySelectorAll('img, svg, canvas, video, iframe').forEach(function (el) {
            if (shouldSkip(el)) return;
            el.classList.add('mobile-media-fluid');
        });
    }

    function normalizeState() {
        document.body.classList.toggle('mobile-hardening-active', isMobile());
        if (!isMobile()) return;
        wrapTables();
        normalizeInlineWidths();
        normalizeComputedLayouts();
        normalizeMedia();
    }

    let resizeTimer = null;
    document.addEventListener('DOMContentLoaded', normalizeState);
    window.addEventListener('resize', function () {
        clearTimeout(resizeTimer);
        resizeTimer = window.setTimeout(normalizeState, 140);
    });
})();
