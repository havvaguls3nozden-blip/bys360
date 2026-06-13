/* BYS360_CORPORATE_PORTAL_MATURITY_V1_6_JS */
(function () {
  var visibilityText = {
    public: 'Herkese açık paylaşım, kurum içindeki tüm yetkili kullanıcıların yayın akışında görünür.',
    only_me: 'Sadece ben seçeneğinde paylaşım kişisel portal duvarınızda size görünür.',
    unit: 'Birim içi paylaşım, birim kapsamına göre gösterilir.',
    upper_unit: 'Üst birim kapsamı, ilgili üst organizasyon yapısındaki kullanıcılara yöneliktir.',
    selected_users: 'Belirli kişiler seçeneğinde yalnızca seçtiğiniz kullanıcılar paylaşımı görür.',
    group: 'Grup paylaşımı, seçili portal grubunun akışında ve üyelerin yetkili akışında görünür.',
    role: 'Rol bazlı paylaşım, seçili rol kapsamındaki kullanıcılara gösterilir.'
  };

  function refreshComposer(form) {
    var select = form.querySelector('[data-portal-visibility]');
    if (!select) return;
    var value = select.value;
    form.querySelectorAll('[data-portal-target]').forEach(function (panel) {
      panel.style.display = panel.getAttribute('data-portal-target') === value ? 'block' : 'none';
    });
    var help = form.querySelector('[data-portal-visibility-help] span');
    if (help) help.textContent = visibilityText[value] || 'Görünürlük seçiminiz yetki kontrollü uygulanır.';
  }

  function refreshCounter(field) {
    var counterId = field.getAttribute('data-portal-counter');
    if (!counterId) return;
    var counter = document.getElementById(counterId);
    if (!counter) return;
    var max = field.getAttribute('maxlength') || '4000';
    counter.textContent = (field.value || '').length + ' / ' + max;
  }

  document.querySelectorAll('.portal-composer-form').forEach(function (form) {
    refreshComposer(form);
    var select = form.querySelector('[data-portal-visibility]');
    if (select) select.addEventListener('change', function () { refreshComposer(form); });
    form.querySelectorAll('[data-portal-counter]').forEach(function (field) {
      refreshCounter(field);
      field.addEventListener('input', function () { refreshCounter(field); });
    });
    form.addEventListener('submit', function () {
      var btn = form.querySelector('[data-portal-submit]');
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Yayınlanıyor';
      }
    });
  });

  document.querySelectorAll('[data-portal-inline-form], [data-portal-quick-action]').forEach(function (form) {
    form.addEventListener('submit', function () {
      var btn = form.querySelector('button[type="submit"]');
      if (btn) btn.disabled = true;
    });
  });
})();


// BYS360_CORPORATE_PORTAL_MEDIA_VIDEO_V2_3_JS
(function () {
  document.querySelectorAll('[data-portal-images]').forEach(function (input) {
    var wrap = input.closest('.portal-media-field');
    var counter = wrap && wrap.querySelector('[data-portal-image-count]');
    input.addEventListener('change', function () {
      if (!counter) return;
      var count = input.files ? input.files.length : 0;
      counter.style.display = count ? 'inline-block' : 'none';
      counter.textContent = count ? (count + ' görsel seçildi') : '';
      if (count > 6) counter.textContent = 'En fazla 6 görsel eklenir; ilk 6 dosya işlenecek.';
    });
  });
})();
// /BYS360_CORPORATE_PORTAL_MEDIA_VIDEO_V2_3_JS
// BYS360_PORTAL_COMPOSER_ACCORDION_V2_6_BEGIN
(function () {
  function ready(fn){ if(document.readyState !== 'loading'){ fn(); } else { document.addEventListener('DOMContentLoaded', fn); } }
  ready(function(){
    document.querySelectorAll('[data-portal-composer-details]').forEach(function(details){
      var form = details.querySelector('.portal-composer-form');
      var body = form && form.querySelector('#portal-body');
      details.addEventListener('toggle', function(){
        if(details.open && body){ setTimeout(function(){ body.focus({preventScroll:true}); }, 80); }
      });
    });
    document.querySelectorAll('a[href="#portal-body"], a[href="#new-post"], [data-open-portal-composer]').forEach(function(link){
      link.addEventListener('click', function(){
        var details = document.querySelector('[data-portal-composer-details]');
        if(details){ details.open = true; }
      });
    });
  });
})();
// BYS360_PORTAL_COMPOSER_ACCORDION_V2_6_END

// BYS360_PORTAL_MEDIA_COMMENTS_MENTIONS_V2_12_1_JS
(function () {
  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  function ensureMentionMenu() {
    var menu = document.querySelector('.portal-mention-menu');
    if (!menu) {
      menu = document.createElement('div');
      menu.className = 'portal-mention-menu';
      menu.setAttribute('role', 'listbox');
      menu.hidden = true;
      document.body.appendChild(menu);
    }
    return menu;
  }

  function activeMentionQuery(input) {
    var pos = input.selectionStart || 0;
    var text = input.value || '';
    var before = text.slice(0, pos);
    var at = before.lastIndexOf('@');
    if (at < 0) return null;
    var term = before.slice(at + 1);
    if (/\s{2,}/.test(term) || term.indexOf('\n') >= 0) return null;
    if (term.length > 60) return null;
    return { start: at, end: pos, query: term.trim() };
  }

  function addMentionHidden(form, item) {
    if (!form || !item || !item.id) return;
    var wrap = form.querySelector('[data-portal-mention-hidden]') || form;
    var exists = wrap.querySelector('input[name="mention_user_ids"][value="' + item.id + '"]');
    if (exists) return;
    var input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'mention_user_ids';
    input.value = String(item.id);
    wrap.appendChild(input);
    var chip = document.createElement('span');
    chip.className = 'portal-mention-chip';
    chip.textContent = '@' + (item.label || 'Personel');
    wrap.appendChild(chip);
  }

  function placeMenu(input, menu) {
    var rect = input.getBoundingClientRect();
    menu.style.left = Math.max(12, rect.left) + 'px';
    menu.style.top = (rect.bottom + 6) + 'px';
    menu.style.width = Math.max(260, Math.min(rect.width, 420)) + 'px';
  }

  function closeMenu(menu) {
    if (menu) {
      menu.hidden = true;
      menu.innerHTML = '';
      menu._activeInput = null;
    }
  }

  function renderMentionItems(input, menu, items, context) {
    menu.innerHTML = '';
    if (!items || !items.length) {
      var empty = document.createElement('div');
      empty.className = 'portal-mention-empty';
      empty.textContent = 'Personel bulunamadı.';
      menu.appendChild(empty);
      menu.hidden = false;
      placeMenu(input, menu);
      return;
    }
    items.forEach(function (item) {
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'portal-mention-item';
      button.setAttribute('role', 'option');
      var title = document.createElement('strong');
      title.textContent = item.label || 'BYS360 Kullanıcısı';
      var sub = document.createElement('small');
      sub.textContent = item.subtitle || 'Kurumsal portal kullanıcısı';
      button.appendChild(title);
      button.appendChild(sub);
      button.addEventListener('mousedown', function (ev) {
        ev.preventDefault();
        var value = input.value || '';
        var insert = item.insert || ('@' + (item.label || 'Personel'));
        input.value = value.slice(0, context.start) + insert + ' ' + value.slice(context.end);
        var newPos = context.start + insert.length + 1;
        input.focus();
        try { input.setSelectionRange(newPos, newPos); } catch (e) {}
        addMentionHidden(input.closest('form'), item);
        closeMenu(menu);
      });
      menu.appendChild(button);
    });
    menu.hidden = false;
    menu._activeInput = input;
    placeMenu(input, menu);
  }

  function fetchMentions(input) {
    var context = activeMentionQuery(input);
    var menu = ensureMentionMenu();
    if (!context) { closeMenu(menu); return; }
    var url = '/portal/mentions/users?q=' + encodeURIComponent(context.query || '');
    fetch(url, { headers: { 'Accept': 'application/json' }, credentials: 'same-origin' })
      .then(function (response) { return response.ok ? response.json() : { items: [] }; })
      .then(function (data) { renderMentionItems(input, menu, data.items || [], context); })
      .catch(function () { closeMenu(menu); });
  }

  ready(function () {
    document.querySelectorAll('[data-portal-video-file]').forEach(function (input) {
      var wrap = input.closest('.portal-media-field');
      var counter = wrap && wrap.querySelector('[data-portal-video-count]');
      input.addEventListener('change', function () {
        if (!counter) return;
        var file = input.files && input.files[0];
        counter.style.display = file ? 'inline-block' : 'none';
        counter.textContent = file ? ('Video seçildi: ' + file.name) : '';
      });
    });

    document.addEventListener('click', function (ev) {
      var toggle = ev.target.closest('[data-portal-reply-toggle]');
      if (toggle) {
        var id = toggle.getAttribute('data-portal-reply-toggle');
        var form = id && document.getElementById(id);
        if (form) {
          form.hidden = !form.hidden;
          if (!form.hidden) {
            var input = form.querySelector('[data-portal-mention]');
            if (input) input.focus({ preventScroll: true });
          }
        }
        return;
      }
      var menu = document.querySelector('.portal-mention-menu');
      if (menu && !ev.target.closest('.portal-mention-menu') && !ev.target.closest('[data-portal-mention]')) {
        closeMenu(menu);
      }
    });

    var mentionTimer = null;
    document.querySelectorAll('[data-portal-mention]').forEach(function (input) {
      input.addEventListener('input', function () {
        clearTimeout(mentionTimer);
        mentionTimer = setTimeout(function () { fetchMentions(input); }, 180);
      });
      input.addEventListener('keydown', function (ev) {
        if (ev.key === 'Escape') closeMenu(document.querySelector('.portal-mention-menu'));
      });
      input.addEventListener('blur', function () {
        setTimeout(function () { closeMenu(document.querySelector('.portal-mention-menu')); }, 180);
      });
    });
  });
})();
// /BYS360_PORTAL_MEDIA_COMMENTS_MENTIONS_V2_12_1_JS
