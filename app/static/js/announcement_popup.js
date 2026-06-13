(function(){
  'use strict';

  function ready(fn){
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fn);
    else fn();
  }

  function text(node, value){
    if (node) node.textContent = value || '';
  }

  function setStatus(root, message){
    text(root.querySelector('[data-announcement-status]'), message || '');
  }

  function stopMedia(root){
    var box = root.querySelector('[data-announcement-media]');
    if (box) box.innerHTML = '';
  }

  function closePopup(root){
    stopMedia(root);
    root.classList.remove('is-open','is-required');
    root.removeAttribute('data-announcement-id');
    root.removeAttribute('data-announcement-type');
    document.body.classList.remove('bys-announcement-open');
  }

  function postAction(url, token, csrfToken){
    var body = new FormData();
    body.append('runtime_token', token || '');
    if (csrfToken) body.append('csrf_token', csrfToken);
    return fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: {'X-Requested-With': 'XMLHttpRequest', 'X-BYS360-Announcement-Token': token || '', 'X-CSRFToken': csrfToken || '', 'X-CSRF-Token': csrfToken || ''},
      body: body
    }).then(function(resp){ return resp.json().then(function(data){ return {status: resp.status, data: data}; }); });
  }

  function createSafeLink(url, label){
    var link = document.createElement('a');
    link.href = url;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.textContent = label || url;
    return link;
  }

  function renderVideoEmbed(box, item){
    var frameWrap = document.createElement('div');
    frameWrap.className = 'bys-announcement-video-frame';
    var iframe = document.createElement('iframe');
    iframe.src = item.media_embed_url;
    iframe.title = item.title || 'BYS360 video duyurusu';
    iframe.loading = 'lazy';
    iframe.referrerPolicy = 'strict-origin-when-cross-origin';
    iframe.allow = 'accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
    iframe.allowFullscreen = true;
    iframe.setAttribute('sandbox', 'allow-scripts allow-same-origin allow-presentation allow-popups');
    frameWrap.appendChild(iframe);
    box.appendChild(frameWrap);
  }

  function renderUploadedVideo(box, item){
    var video = document.createElement('video');
    video.className = 'bys-announcement-video';
    video.controls = true;
    video.preload = 'metadata';
    video.controlsList = 'nodownload';
    if (item.cover_image_path) video.poster = item.cover_image_path;
    var source = document.createElement('source');
    source.src = item.media_file_url || item.media_url;
    source.type = (source.src || '').toLowerCase().indexOf('.webm') !== -1 ? 'video/webm' : 'video/mp4';
    video.appendChild(source);
    box.appendChild(video);
  }

  function renderImage(box, item){
    var img = document.createElement('img');
    img.className = 'bys-announcement-image';
    img.src = item.media_url;
    img.alt = item.title || 'BYS360 duyuru görseli';
    img.loading = 'lazy';
    box.appendChild(img);
  }

  function renderPdf(box, item){
    var card = document.createElement('div');
    card.className = 'bys-announcement-file-card';
    var icon = document.createElement('span');
    icon.className = 'bys-announcement-file-icon';
    icon.innerHTML = '<i class="fa-solid fa-file-pdf"></i>';
    var content = document.createElement('div');
    var title = document.createElement('strong');
    title.textContent = 'PDF duyuru eki';
    var desc = document.createElement('p');
    desc.textContent = 'Dosyayı yeni sekmede açabilirsiniz.';
    content.appendChild(title);
    content.appendChild(desc);
    var link = createSafeLink(item.media_url, 'PDF Aç');
    link.className = 'bys-announcement-file-link';
    card.appendChild(icon);
    card.appendChild(content);
    card.appendChild(link);
    box.appendChild(card);
  }

  function mediaFallback(box, item){
    var label = document.createElement('div');
    label.textContent = item.media_label || 'Medya bağlantısı';
    box.appendChild(label);
    if (item.media_url) box.appendChild(createSafeLink(item.media_url, item.media_url));
  }

  function renderMedia(root, item){
    var box = root.querySelector('[data-announcement-media]');
    if (!box) return;
    box.innerHTML = '';
    box.hidden = true;
    if (!item || item.media_type === 'none') return;

    try {
      if (item.media_kind === 'embed_video' && item.media_embed_url) {
        renderVideoEmbed(box, item);
      } else if (item.media_kind === 'upload_video' && (item.media_file_url || item.media_url)) {
        renderUploadedVideo(box, item);
      } else if (item.media_kind === 'image' && item.media_url) {
        renderImage(box, item);
      } else if (item.media_kind === 'pdf' && item.media_url) {
        renderPdf(box, item);
      } else if (item.media_url) {
        mediaFallback(box, item);
      } else {
        return;
      }
      box.hidden = false;
    } catch (err) {
      box.innerHTML = '';
      if (item.media_url) {
        mediaFallback(box, item);
        box.hidden = false;
      }
    }
  }

  function openPopup(root, item){
    root.dataset.announcementId = item.id;
    root.dataset.announcementType = item.type || 'info';
    root.classList.toggle('is-required', !!item.is_required);
    text(root.querySelector('[data-announcement-title]'), item.title || 'Duyuru');
    text(root.querySelector('[data-announcement-body]'), item.body || '');
    text(root.querySelector('[data-announcement-type-label]'), item.type_label || 'BYS360 Duyuru');
    text(root.querySelector('[data-announcement-required-note]'), item.is_required ? 'Zorunlu duyuru · Okudum onayı gerekir' : 'Bilgilendirme duyurusu');
    text(root.querySelector('[data-announcement-ack]'), item.button_text || 'Okudum');

    renderMedia(root, item);

    var cta = root.querySelector('[data-announcement-cta]');
    if (cta) {
      if (item.cta_url) {
        cta.hidden = false;
        cta.href = item.cta_url;
        cta.textContent = item.cta_text || 'Detaya Git';
      } else {
        cta.hidden = true;
        cta.removeAttribute('href');
      }
    }

    setStatus(root, '');
    root.classList.add('is-open');
    document.body.classList.add('bys-announcement-open');
    var modal = root.querySelector('.bys-announcement-modal');
    if (modal) window.setTimeout(function(){ modal.focus(); }, 80);
  }

  function init(){
    var root = document.getElementById('bys-announcement-popup-root');
    if (!root) return;
    var runtimeUrl = root.dataset.runtimeUrl || '';
    var csrfToken = root.dataset.csrfToken || '';
    function getRuntimeToken(){ return root.dataset.token || ''; }
    function setRuntimeToken(value){ if (value) root.dataset.token = value; }
    if (!runtimeUrl) return;

    var ackButton = root.querySelector('[data-announcement-ack]');
    var dismissButton = root.querySelector('[data-announcement-dismiss]');
    var closeNodes = root.querySelectorAll('[data-announcement-close]');

    fetch(runtimeUrl, {credentials: 'same-origin', headers: {'X-Requested-With': 'XMLHttpRequest'}})
      .then(function(resp){ return resp.json(); })
      .then(function(data){
        if (data && data.runtime_token) setRuntimeToken(data.runtime_token);
        if (!data || !data.ok || !data.has_pending || !data.announcement) return;
        openPopup(root, data.announcement);
      })
      .catch(function(){ /* Ana ekran açılışını duyuru kontrolü yüzünden bozma. */ });

    if (ackButton) {
      ackButton.addEventListener('click', function(){
        var id = root.dataset.announcementId;
        if (!id) return;
        ackButton.disabled = true;
        setStatus(root, 'Okundu kaydı yazılıyor...');
        postAction('/announcements/popup/' + encodeURIComponent(id) + '/acknowledge', getRuntimeToken(), csrfToken)
          .then(function(result){
            if (result.data && result.data.ok) closePopup(root);
            else setStatus(root, (result.data && result.data.message) || 'İşlem tamamlanamadı.');
          })
          .catch(function(){ setStatus(root, 'Bağlantı hatası nedeniyle işlem tamamlanamadı.'); })
          .finally(function(){ ackButton.disabled = false; });
      });
    }

    if (dismissButton) {
      dismissButton.addEventListener('click', function(){
        var id = root.dataset.announcementId;
        if (!id) return;
        dismissButton.disabled = true;
        setStatus(root, 'Kapatma kaydı yazılıyor...');
        postAction('/announcements/popup/' + encodeURIComponent(id) + '/dismiss', getRuntimeToken(), csrfToken)
          .then(function(result){
            if (result.data && result.data.ok) closePopup(root);
            else setStatus(root, (result.data && result.data.message) || 'İşlem tamamlanamadı.');
          })
          .catch(function(){ setStatus(root, 'Bağlantı hatası nedeniyle işlem tamamlanamadı.'); })
          .finally(function(){ dismissButton.disabled = false; });
      });
    }

    Array.prototype.forEach.call(closeNodes, function(node){
      node.addEventListener('click', function(){
        if (root.classList.contains('is-required')) return;
        if (dismissButton) dismissButton.click();
        else closePopup(root);
      });
    });

    document.addEventListener('keydown', function(event){
      if (event.key !== 'Escape') return;
      if (!root.classList.contains('is-open')) return;
      if (root.classList.contains('is-required')) return;
      if (dismissButton) dismissButton.click();
      else closePopup(root);
    });
  }

  ready(init);
})();
