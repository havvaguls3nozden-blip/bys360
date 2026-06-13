(function () {
  function bindUnifiedSearch(inputId) {
    var input = document.getElementById(inputId);
    if (!input) return;
    input.addEventListener('input', function () {
      var q = (input.value || '').toLowerCase().trim();
      document.querySelectorAll('[data-search-target]').forEach(function (node) {
        var text = (node.getAttribute('data-search-target') || '').toLowerCase();
        node.style.display = (!q || text.indexOf(q) !== -1) ? '' : 'none';
      });
    });
  }

  function bindFocusAssist() {
    if (window.innerWidth > 768) return;
    document.querySelectorAll('.perf-form-shell textarea, .perf-form-shell select, .perf-form-shell input').forEach(function (field) {
      field.addEventListener('focus', function () {
        window.setTimeout(function () {
          try {
            field.scrollIntoView({ behavior: 'smooth', block: 'center' });
          } catch (err) {}
        }, 220);
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    bindUnifiedSearch('compareSearch');
    bindFocusAssist();
  });
})();
