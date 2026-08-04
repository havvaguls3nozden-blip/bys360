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



  // BYS360_MESSAGE_INTERACTIONS_V1_JS
  function messageCsrfToken(){
    const input = document.querySelector('input[name="csrf_token"]');
    return input ? input.value : '';
  }

  function showMessageInlineFeedback(form, text, type){
    if(!form) return;
    let box = form.querySelector('.msg-inline-feedback');
    if(!box){
      box = document.createElement('div');
      box.className = 'msg-inline-feedback';
      form.appendChild(box);
    }
    box.textContent = text || '';
    box.dataset.type = type || 'info';
    box.hidden = !text;
  }

  function renderReactionSummary(holder, reactions){
    if(!holder) return;
    holder.innerHTML = '';
    (reactions || []).forEach(function(item){
      const pill = document.createElement('span');
      pill.className = 'msg-reaction-pill' + (item.mine ? ' mine' : '');
      const emoji = document.createElement('span');
      emoji.textContent = item.emoji || '';
      const count = document.createElement('strong');
      count.textContent = String(item.count || 0);
      pill.appendChild(emoji);
      pill.appendChild(count);
      holder.appendChild(pill);
    });
  }

  function renderCommentItem(comment){
    const item = document.createElement('div');
    item.className = 'msg-comment-item';
    if(comment && comment.id){ item.dataset.commentId = String(comment.id); }
    const name = document.createElement('strong');
    name.textContent = (comment && comment.user_name) || 'Kullanıcı';
    const body = document.createElement('span');
    body.textContent = (comment && comment.body) || '';
    const date = document.createElement('small');
    date.textContent = (comment && comment.created_at_label) || '-';
    item.appendChild(name);
    item.appendChild(body);
    item.appendChild(date);
    return item;
  }

  function renderAttachmentElement(attachment){
    const url = attachment.preview_url || attachment.download_url || '#';
    const name = attachment.original_filename || 'Dosya';
    if(attachment.is_image){
      const a = document.createElement('a');
      a.className = 'msg-attachment is-image';
      a.href = url;
      a.target = '_blank';
      const img = document.createElement('img');
      img.src = url;
      img.alt = name;
      a.appendChild(img);
      return a;
    }
    const a = document.createElement('a');
    a.className = 'msg-attachment';
    a.href = attachment.download_url || url;
    a.target = '_blank';
    const icon = document.createElement('i');
    icon.className = attachment.icon_class || 'fa-solid fa-paperclip';
    const span = document.createElement('span');
    span.textContent = name;
    a.appendChild(icon);
    a.appendChild(span);
    return a;
  }

  function buildMessageActions(message){
    const interactions = document.createElement('div');
    interactions.className = 'msg-interactions';
    interactions.dataset.messageInteractions = '1';
    interactions.dataset.messageId = String(message.id || '');

    const summary = document.createElement('div');
    summary.className = 'msg-reaction-summary';
    summary.dataset.messageReactions = '1';
    renderReactionSummary(summary, message.reactions || []);
    interactions.appendChild(summary);

    const actions = document.createElement('div');
    actions.className = 'msg-reaction-actions';
    (message.reaction_options || ['👍','👎','❤️','👏','✅']).forEach(function(emoji){
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = '/messages/' + encodeURIComponent(message.id) + '/react';
      form.className = 'js-message-reaction-form';
      form.dataset.messageId = String(message.id || '');
      const csrf = document.createElement('input');
      csrf.type = 'hidden'; csrf.name = 'csrf_token'; csrf.value = messageCsrfToken();
      const reaction = document.createElement('input');
      reaction.type = 'hidden'; reaction.name = 'reaction'; reaction.value = emoji;
      const btn = document.createElement('button');
      btn.type = 'submit'; btn.className = 'msg-reaction-btn'; btn.textContent = emoji;
      form.appendChild(csrf); form.appendChild(reaction); form.appendChild(btn);
      actions.appendChild(form);
    });
    const commentBtn = document.createElement('button');
    commentBtn.type = 'button';
    commentBtn.className = 'msg-reaction-btn comment-toggle';
    commentBtn.dataset.messageCommentToggle = '1';
    commentBtn.dataset.messageId = String(message.id || '');
    commentBtn.innerHTML = '<i class="fa-regular fa-comment"></i> Yorum';
    actions.appendChild(commentBtn);
    interactions.appendChild(actions);

    const comments = document.createElement('div');
    comments.className = 'msg-comments';
    comments.dataset.messageComments = '1';
    (message.comments || []).forEach(function(comment){ comments.appendChild(renderCommentItem(comment)); });
    interactions.appendChild(comments);

    const cform = document.createElement('form');
    cform.method = 'POST';
    cform.action = '/messages/' + encodeURIComponent(message.id) + '/comment';
    cform.className = 'msg-comment-form js-message-comment-form';
    cform.dataset.messageId = String(message.id || '');
    cform.hidden = true;
    const csrf = document.createElement('input'); csrf.type = 'hidden'; csrf.name = 'csrf_token'; csrf.value = messageCsrfToken();
    const input = document.createElement('input'); input.type = 'text'; input.name = 'body'; input.maxLength = 1200; input.autocomplete = 'off'; input.placeholder = 'Bu mesaja yorum yazın...';
    const send = document.createElement('button'); send.type = 'submit'; send.innerHTML = '<i class="fa-solid fa-paper-plane"></i>';
    cform.appendChild(csrf); cform.appendChild(input); cform.appendChild(send);
    interactions.appendChild(cform);
    return interactions;
  }

  function appendMessageToList(message){
    const box = document.getElementById('msgMessages');
    if(!box || !message) return;
    const empty = box.querySelector('.msg-empty');
    if(empty){ empty.remove(); }

    const row = document.createElement('div');
    row.className = 'msg-row' + (message.is_mine ? ' mine' : '');
    row.dataset.messageRow = '1';
    row.dataset.messageId = String(message.id || '');

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';

    const author = document.createElement('div');
    author.className = 'msg-author';
    author.textContent = message.sender_name || 'Kullanıcı';
    bubble.appendChild(author);

    if(message.body){
      const text = document.createElement('div');
      text.className = 'msg-text';
      text.textContent = message.body;
      bubble.appendChild(text);
    }

    if(message.attachments && message.attachments.length){
      const attachments = document.createElement('div');
      attachments.className = 'msg-attachments';
      message.attachments.forEach(function(attachment){ attachments.appendChild(renderAttachmentElement(attachment)); });
      bubble.appendChild(attachments);
    }

    const meta = document.createElement('div');
    meta.className = 'msg-meta';
    const date = document.createElement('span');
    date.textContent = message.sent_at_label || '-';
    meta.appendChild(date);
    bubble.appendChild(meta);
    bubble.appendChild(buildMessageActions(message));

    row.appendChild(bubble);
    box.appendChild(row);
    decorateMessageLinks();
    scrollMessagesToBottom();
  }

  function resetComposeForm(form, payload){
    const textarea = form.querySelector('textarea[name="body"]');
    if(textarea){ textarea.value = ''; autogrow(textarea); }
    const fileInput = form.querySelector('.js-message-attachment-input');
    if(fileInput){ fileInput.value = ''; }
    const preview = form.querySelector('.js-message-attachment-preview');
    if(preview){ preview.innerHTML = ''; preview.hidden = true; }
    const token = form.querySelector('input[name="_form_token"]');
    if(token && payload && payload.next_form_token){ token.value = payload.next_form_token; }
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
        const textarea = form.querySelector('textarea[name="body"]');
        const files = fileInput ? Array.from(fileInput.files || []) : [];
        const body = textarea ? (textarea.value || '').trim() : '';
        if(!body && !files.length){
          event.preventDefault();
          if(textarea){ textarea.focus(); }
          return false;
        }
        event.preventDefault();
        if(submitted){ return false; }
        submitted = true;
        const btn = form.querySelector('.msg-send');
        if(btn){
          btn.disabled = true;
          btn.classList.add('is-busy');
        }
        showMessageInlineFeedback(form, 'Mesaj gönderiliyor...', 'info');
        fetch(form.action, {
          method: 'POST',
          body: new FormData(form),
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json'
          },
          credentials: 'same-origin'
        }).then(function(response){
          return response.json().catch(function(){ return {}; }).then(function(payload){
            if(!response.ok || !payload.ok){
              throw payload || { message: 'Mesaj gönderilemedi.' };
            }
            return payload;
          });
        }).then(function(payload){
          if(payload.sent_message){ appendMessageToList(payload.sent_message); }
          resetComposeForm(form, payload);
          showMessageInlineFeedback(form, payload.message || 'Mesaj gönderildi.', 'success');
          setTimeout(function(){ showMessageInlineFeedback(form, '', 'info'); }, 1800);
        }).catch(function(error){
          showMessageInlineFeedback(form, (error && error.message) || 'Mesaj gönderilemedi. Lütfen tekrar deneyin.', 'error');
        }).finally(function(){
          submitted = false;
          if(btn){
            btn.disabled = false;
            btn.classList.remove('is-busy');
          }
        });
        return false;
      });
    });

    document.addEventListener('submit', function(event){
      const confirmForm = event.target.closest('form[data-confirm]');
      if(confirmForm){
        const message = confirmForm.getAttribute('data-confirm');
        if(message && !window.confirm(message)){
          event.preventDefault();
        }
        return;
      }

      const reactionForm = event.target.closest('.js-message-reaction-form');
      if(reactionForm){
        event.preventDefault();
        const messageId = reactionForm.dataset.messageId || '';
        const btn = reactionForm.querySelector('button');
        if(btn){ btn.disabled = true; }
        fetch(reactionForm.action, {
          method: 'POST',
          body: new FormData(reactionForm),
          headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' },
          credentials: 'same-origin'
        }).then(function(response){
          return response.json().catch(function(){ return {}; }).then(function(payload){
            if(!response.ok || !payload.ok){ throw payload || {}; }
            return payload;
          });
        }).then(function(payload){
          const root = document.querySelector('[data-message-interactions][data-message-id="' + CSS.escape(String(messageId || payload.message_id || '')) + '"]');
          renderReactionSummary(root ? root.querySelector('[data-message-reactions]') : null, payload.reactions || []);
        }).catch(function(){
          window.alert('Tepki kaydedilemedi. Lütfen tekrar deneyin.');
        }).finally(function(){
          if(btn){ btn.disabled = false; }
        });
        return false;
      }

      const commentForm = event.target.closest('.js-message-comment-form');
      if(commentForm){
        event.preventDefault();
        const input = commentForm.querySelector('input[name="body"]');
        const body = input ? (input.value || '').trim() : '';
        if(!body){ if(input){ input.focus(); } return false; }
        const btn = commentForm.querySelector('button');
        if(btn){ btn.disabled = true; }
        fetch(commentForm.action, {
          method: 'POST',
          body: new FormData(commentForm),
          headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' },
          credentials: 'same-origin'
        }).then(function(response){
          return response.json().catch(function(){ return {}; }).then(function(payload){
            if(!response.ok || !payload.ok){ throw payload || {}; }
            return payload;
          });
        }).then(function(payload){
          const root = document.querySelector('[data-message-interactions][data-message-id="' + CSS.escape(String(payload.message_id || commentForm.dataset.messageId || '')) + '"]');
          const list = root ? root.querySelector('[data-message-comments]') : null;
          if(list && payload.comment){ list.appendChild(renderCommentItem(payload.comment)); }
          if(input){ input.value = ''; input.focus(); }
        }).catch(function(error){
          window.alert((error && error.message) || 'Yorum eklenemedi. Lütfen tekrar deneyin.');
        }).finally(function(){
          if(btn){ btn.disabled = false; }
        });
        return false;
      }
    });

    document.addEventListener('click', function(event){
      const editTrigger = event.target.closest('[data-message-edit-trigger]');
      if(editTrigger){
        if (typeof window.openEditModal === 'function') {
          window.openEditModal(editTrigger.getAttribute('data-message-id'), editTrigger.getAttribute('data-message-body'));
        }
        return;
      }

      const toggle = event.target.closest('[data-message-comment-toggle]');
      if(!toggle) return;
      const messageId = toggle.dataset.messageId || '';
      const root = document.querySelector('[data-message-interactions][data-message-id="' + CSS.escape(String(messageId)) + '"]');
      const form = root ? root.querySelector('.js-message-comment-form') : null;
      if(!form) return;
      form.hidden = !form.hidden;
      if(!form.hidden){
        const input = form.querySelector('input[name="body"]');
        if(input){ input.focus(); }
      }
    });

    const messageContainer = document.getElementById('msgMessages');
    if(messageContainer && window.MutationObserver){
      const observer = new MutationObserver(function(){ decorateMessageLinks(); });
      observer.observe(messageContainer, { childList:true, subtree:true });
    }
  });

  window.BYS360DecorateMessageLinks = decorateMessageLinks;
})();
