(function(){
  function autogrow(textarea){
    if(!textarea) return;
    textarea.style.height = 'auto';
    const next = Math.min(Math.max(textarea.scrollHeight, 46), 180);
    textarea.style.height = next + 'px';
  }

  function scrollMessagesToBottom(){
    const threadBox = document.getElementById('msgMessages');
    if(!threadBox) return;
    setTimeout(function(){
      try { threadBox.scrollTop = threadBox.scrollHeight; } catch(err) {}
      try { window.scrollTo({ top: document.body.scrollHeight, behavior: 'auto' }); } catch(err) {}
    }, 80);
  }

  function trimTrailingUrlPunctuation(value){
    let raw = String(value || '');
    let trailing = '';
    while(raw && /[.,!?;:)\]\}]/.test(raw.slice(-1))){
      trailing = raw.slice(-1) + trailing;
      raw = raw.slice(0, -1);
    }
    return { url: raw, trailing: trailing };
  }

  function normalizeUrl(value){
    const cleaned = trimTrailingUrlPunctuation(value).url;
    if(!cleaned) return null;
    const candidate = /^https?:\/\//i.test(cleaned) ? cleaned : 'https://' + cleaned;
    try {
      const parsed = new URL(candidate);
      if(!/^https?:$/i.test(parsed.protocol)) return null;
      return parsed;
    } catch(err){
      return null;
    }
  }

  function safeVideoId(value, pattern){
    const raw = String(value || '').trim();
    if(!pattern.test(raw)) return null;
    return raw;
  }

  function buildEmbedPayload(url){
    if(!url) return null;
    const host = (url.hostname || '').replace(/^www\./i, '').toLowerCase();
    const path = (url.pathname || '').replace(/^\/+/, '');

    if(host === 'youtu.be'){
      const id = safeVideoId(path.split('/')[0], /^[A-Za-z0-9_-]{6,20}$/);
      if(id){
        return {
          provider: 'YouTube',
          embedUrl: 'https://www.youtube-nocookie.com/embed/' + encodeURIComponent(id),
          originalUrl: url.href
        };
      }
    }

    if(host === 'youtube.com' || host.endsWith('.youtube.com') || host === 'youtube-nocookie.com' || host.endsWith('.youtube-nocookie.com')){
      let id = url.searchParams.get('v') || '';
      const parts = path.split('/');
      if(!id && ['shorts','embed','live'].indexOf(parts[0]) !== -1){
        id = parts[1] || '';
      }
      id = safeVideoId(id, /^[A-Za-z0-9_-]{6,20}$/);
      if(id){
        return {
          provider: 'YouTube',
          embedUrl: 'https://www.youtube-nocookie.com/embed/' + encodeURIComponent(id),
          originalUrl: url.href
        };
      }
    }

    if(host === 'vimeo.com' || host.endsWith('.vimeo.com')){
      const parts = path.split('/').filter(Boolean);
      let id = '';
      if(host === 'player.vimeo.com' && parts[0] === 'video'){
        id = parts[1] || '';
      } else {
        id = parts.find(function(part){ return /^\d{5,15}$/.test(part); }) || '';
      }
      id = safeVideoId(id, /^\d{5,15}$/);
      if(id){
        return {
          provider: 'Vimeo',
          embedUrl: 'https://player.vimeo.com/video/' + encodeURIComponent(id),
          originalUrl: url.href
        };
      }
    }

    if(host === 'dai.ly'){
      const id = safeVideoId(path.split('/')[0], /^[A-Za-z0-9_-]{4,20}$/i);
      if(id){
        return {
          provider: 'Dailymotion',
          embedUrl: 'https://www.dailymotion.com/embed/video/' + encodeURIComponent(id),
          originalUrl: url.href
        };
      }
    }

    if(host === 'dailymotion.com' || host.endsWith('.dailymotion.com')){
      const parts = path.split('/');
      const videoIndex = parts.indexOf('video');
      let id = videoIndex !== -1 ? (parts[videoIndex + 1] || '') : '';
      id = (id || '').split('_')[0];
      id = safeVideoId(id, /^[A-Za-z0-9_-]{4,20}$/);
      if(id){
        return {
          provider: 'Dailymotion',
          embedUrl: 'https://www.dailymotion.com/embed/video/' + encodeURIComponent(id),
          originalUrl: url.href
        };
      }
    }

    return null;
  }

  function createLinkElement(displayText, parsedUrl){
    const a = document.createElement('a');
    a.className = 'msg-inline-link';
    a.href = parsedUrl.href;
    a.target = '_blank';
    a.rel = 'noopener noreferrer nofollow';
    a.textContent = displayText;
    return a;
  }

  function createEmbedCard(payload){
    const card = document.createElement('div');
    card.className = 'msg-video-embed-card';
    card.dataset.provider = payload.provider || 'Video';

    const head = document.createElement('div');
    head.className = 'msg-video-embed-head';

    const icon = document.createElement('span');
    icon.className = 'msg-video-embed-icon';
    icon.innerHTML = '<i class="fa-solid fa-play"></i>';

    const title = document.createElement('span');
    title.className = 'msg-video-embed-title';
    title.textContent = (payload.provider || 'Video') + ' önizlemesi';

    const open = document.createElement('a');
    open.className = 'msg-video-embed-open';
    open.href = payload.originalUrl;
    open.target = '_blank';
    open.rel = 'noopener noreferrer nofollow';
    open.textContent = 'Aç';

    head.appendChild(icon);
    head.appendChild(title);
    head.appendChild(open);

    const ratio = document.createElement('div');
    ratio.className = 'msg-video-embed-ratio';

    const iframe = document.createElement('iframe');
    iframe.src = payload.embedUrl;
    iframe.title = title.textContent;
    iframe.loading = 'lazy';
    iframe.referrerPolicy = 'strict-origin-when-cross-origin';
    iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
    iframe.setAttribute('allowfullscreen', 'allowfullscreen');

    ratio.appendChild(iframe);
    card.appendChild(head);
    card.appendChild(ratio);
    return card;
  }

  function decorateMessageLinks(){
    const urlPattern = /(https?:\/\/[^\s<>'"]+|www\.[^\s<>'"]+)/gi;
    const textBlocks = document.querySelectorAll('.msg-text');
    textBlocks.forEach(function(block){
      if(!block || block.dataset.linkPreviewDecorated === '1') return;
      const sourceText = block.textContent || '';
      if(!urlPattern.test(sourceText)) return;
      urlPattern.lastIndex = 0;

      const fragment = document.createDocumentFragment();
      const embeds = [];
      let lastIndex = 0;
      let match;

      while((match = urlPattern.exec(sourceText)) !== null){
        const rawMatch = match[0];
        const parts = trimTrailingUrlPunctuation(rawMatch);
        const parsed = normalizeUrl(parts.url);
        const start = match.index;
        const end = start + rawMatch.length;

        if(start > lastIndex){
          fragment.appendChild(document.createTextNode(sourceText.slice(lastIndex, start)));
        }

        if(parsed){
          fragment.appendChild(createLinkElement(parts.url, parsed));
          const embed = buildEmbedPayload(parsed);
          if(embed && embeds.length < 3){
            embeds.push(embed);
          }
        } else {
          fragment.appendChild(document.createTextNode(parts.url));
        }

        if(parts.trailing){
          fragment.appendChild(document.createTextNode(parts.trailing));
        }
        lastIndex = end;
      }

      if(lastIndex < sourceText.length){
        fragment.appendChild(document.createTextNode(sourceText.slice(lastIndex)));
      }

      block.textContent = '';
      block.appendChild(fragment);
      block.dataset.linkPreviewDecorated = '1';

      if(embeds.length){
        const holder = document.createElement('div');
        holder.className = 'msg-link-embeds';
        embeds.forEach(function(payload){ holder.appendChild(createEmbedCard(payload)); });
        block.insertAdjacentElement('afterend', holder);
      }
    });
  }

  document.addEventListener('DOMContentLoaded', function(){
    decorateMessageLinks();
    scrollMessagesToBottom();

    document.querySelectorAll('.js-msg-autogrow').forEach(function(textarea){
      autogrow(textarea);
      textarea.addEventListener('input', function(){ autogrow(textarea); });
      textarea.addEventListener('focus', function(){
        setTimeout(function(){
          try { textarea.scrollIntoView({ block:'nearest', behavior:'smooth' }); } catch(err) {}
          scrollMessagesToBottom();
        }, 120);
      });
    });

    const inboxSearch = document.getElementById('msgThreadSearch');
    const items = Array.from(document.querySelectorAll('[data-thread-search]'));
    if(inboxSearch && items.length){
      inboxSearch.addEventListener('input', function(){
        const q = (inboxSearch.value || '').toLocaleLowerCase('tr-TR').trim();
        items.forEach(function(item){
          const hay = (item.getAttribute('data-thread-search') || '').toLocaleLowerCase('tr-TR');
          item.style.display = !q || hay.indexOf(q) !== -1 ? '' : 'none';
        });
      });
    }

    function formatFileSize(bytes){
      const value = Number(bytes || 0);
      if(value >= 1024 * 1024){ return (value / (1024 * 1024)).toFixed(1) + ' MB'; }
      if(value >= 1024){ return Math.round(value / 1024) + ' KB'; }
      return value + ' B';
    }

    function renderAttachmentPreview(form){
      const input = form.querySelector('.js-message-attachment-input');
      const preview = form.querySelector('.js-message-attachment-preview');
      if(!input || !preview) return;
      const files = Array.from(input.files || []);
      preview.innerHTML = '';
      if(!files.length){
        preview.hidden = true;
        return;
      }
      preview.hidden = false;
      files.forEach(function(file){
        const pill = document.createElement('span');
        pill.className = 'msg-attachment-pill';
        pill.title = file.name || 'Dosya';
        pill.innerHTML = '<i class="fa-solid fa-paperclip"></i><span></span><small></small>';
        const name = pill.querySelector('span');
        const size = pill.querySelector('small');
        if(name) name.textContent = file.name || 'Dosya';
        if(size) size.textContent = formatFileSize(file.size);
        preview.appendChild(pill);
      });
    }

    document.querySelectorAll('.msg-compose-form').forEach(function(form){
      let submitted = false;
      const fileInput = form.querySelector('.js-message-attachment-input');
      if(fileInput){
        fileInput.addEventListener('change', function(){ renderAttachmentPreview(form); });
      }
      form.addEventListener('submit', function(event){
        if(submitted){
          event.preventDefault();
          return false;
        }
        const textarea = form.querySelector('textarea[name="body"]');
        const files = fileInput ? Array.from(fileInput.files || []) : [];
        const body = textarea ? (textarea.value || '').trim() : '';
        if(!body && !files.length){
          event.preventDefault();
          if(textarea){ textarea.focus(); }
          return false;
        }
        submitted = true;
        const btn = form.querySelector('.msg-send');
        if(btn){
          btn.disabled = true;
          btn.classList.add('is-busy');
        }
      });
    });

    const messageContainer = document.getElementById('msgMessages');
    if(messageContainer && window.MutationObserver){
      const observer = new MutationObserver(function(){ decorateMessageLinks(); });
      observer.observe(messageContainer, { childList:true, subtree:true });
    }
  });

  window.BYS360DecorateMessageLinks = decorateMessageLinks;
})();
