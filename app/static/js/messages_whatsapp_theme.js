/* =========================================================
   BYS360 - Mesajlar: WhatsApp Tarzı JS v2 (MINIMAL + GÜVENLİ)
   
   Bu versiyon:
   - Mevcut form handler'larına DOKUNMAZ (AJAX, submit vs)
   - Enter'a binding YAPMAZ
   - Textarea'ya binding YAPMAZ
   - Sadece DOM'u okur, tarih ayraçları ekler, tik ekler, biter
   ========================================================= */

(function(){
  'use strict';

  function getDayLabel(dateStr){
    var parts = (dateStr || '').trim().split(/[\s.:]+/);
    if(parts.length < 3) return null;
    var d = parseInt(parts[0],10), m = parseInt(parts[1],10) - 1, y = parseInt(parts[2],10);
    if(isNaN(d) || isNaN(m) || isNaN(y)) return null;

    var msgDate = new Date(y, m, d);
    var today = new Date(); today.setHours(0,0,0,0);
    var diffDays = Math.round((today - msgDate) / (1000*60*60*24));

    if(diffDays === 0) return 'BUGÜN';
    if(diffDays === 1) return 'DÜN';
    if(diffDays > 0 && diffDays < 7){
      var gunler = ['PAZAR','PAZARTESİ','SALI','ÇARŞAMBA','PERŞEMBE','CUMA','CUMARTESİ'];
      return gunler[msgDate.getDay()];
    }
    var pad = function(n){ return n<10 ? '0'+n : ''+n; };
    return pad(d) + '.' + pad(m+1) + '.' + y;
  }

  function extractTime(dateStr){
    var m = (dateStr || '').match(/(\d{1,2}):(\d{2})/);
    if(!m) return '';
    return (m[1].length < 2 ? '0'+m[1] : m[1]) + ':' + m[2];
  }

  function getDateKey(dateStr){
    var parts = (dateStr || '').trim().split(/[\s.:]+/);
    if(parts.length < 3) return '';
    return parts[2]
         + (parts[1].length < 2 ? '0'+parts[1] : parts[1])
         + (parts[0].length < 2 ? '0'+parts[0] : parts[0]);
  }

  function decorate(){
    var container = document.getElementById('chatMessages')
                 || document.querySelector('.wa-messages')
                 || document.querySelector('.chat-messages');
    if(!container) return;
    if(container.dataset.waDecoratedV2 === '1') return;
    container.dataset.waDecoratedV2 = '1';

    var rows = container.querySelectorAll('.wa-row, .chat-row');
    if(rows.length === 0) return;

    var lastDateKey = '';

    rows.forEach(function(row){
      var meta = row.querySelector('.wa-meta, .chat-meta');
      if(!meta) return;

      if(!meta.dataset.originalText){
        meta.dataset.originalText = meta.textContent || '';
      }
      var metaText = meta.dataset.originalText;

      var dateKey = getDateKey(metaText);
      if(dateKey && dateKey !== lastDateKey){
        var label = getDayLabel(metaText);
        if(label){
          var divider = document.createElement('div');
          divider.className = 'wa-date-divider';
          divider.setAttribute('aria-hidden', 'true');
          divider.innerHTML = '<span class="wa-date-divider-inner">' + label + '</span>';
          row.parentNode.insertBefore(divider, row);
        }
        lastDateKey = dateKey;
      }

      var timeOnly = extractTime(metaText);
      var edited = metaText.indexOf('düzenlendi') >= 0;
      var isMine = row.classList.contains('mine');

      var html = '<span class="wa-time-inline">' + timeOnly + (edited ? ' ✎' : '') + '</span>';
      if(isMine){
        html += '<span class="wa-tick read" aria-label="Görüldü">✓✓</span>';
      }
      meta.innerHTML = html;
    });
  }

  function scrollToBottom(){
    var container = document.getElementById('chatMessages')
                 || document.querySelector('.wa-messages')
                 || document.querySelector('.chat-messages');
    if(!container) return;
    if(container.dataset.waScrolled === '1') return;
    container.dataset.waScrolled = '1';
    setTimeout(function(){
      container.scrollTop = container.scrollHeight;
    }, 60);
  }

  function init(){
    try { decorate(); } catch(e){ /* sessiz */ }
    try { scrollToBottom(); } catch(e){ /* sessiz */ }
  }

  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  window.BYS_WA_REFRESH = function(){
    var container = document.getElementById('chatMessages')
                 || document.querySelector('.wa-messages')
                 || document.querySelector('.chat-messages');
    if(container) container.dataset.waDecoratedV2 = '0';
    try { decorate(); } catch(e){}
  };
})();
