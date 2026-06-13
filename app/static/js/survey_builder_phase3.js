(function(){
  function q(sel, root){ return (root || document).querySelector(sel); }
  function qa(sel, root){ return Array.from((root || document).querySelectorAll(sel)); }
  function esc(v){ return String(v || '').replace(/[&<>"']/g, function(c){ return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c]; }); }
  function onReady(fn){ if(document.readyState === 'loading'){ document.addEventListener('DOMContentLoaded', fn, {once:true}); } else { fn(); } }
  function typeLabel(type){ return ({text:'Metin',single_choice:'Tek seçim',multiple_choice:'Çoklu seçim',rating_5:'1-5 puan',rating_10:'1-10 puan',yes_no:'Evet / Hayır'})[type] || 'Metin'; }

  onReady(function(){
    var root = q('[data-survey-studio="1"]');
    if(!root || root.dataset.phase3Bound === '1') return;
    root.dataset.phase3Bound = '1';

    var form = q('form', root);
    var questionBlock = q('#questionBlock', root);
    var stickyStack = q('.sticky-stack', root);
    var titleInput = q('#title', root);
    var startAtInput = q('#start_at', root);
    var endAtInput = q('#end_at', root);
    var statusSelect = q('select[name="status"]', root);
    var targetType = q('select[name="target_type"]', root);
    var targetRoleSelect = q('#targetRoleSelect', root);
    var targetUnitSelect = q('#targetUnitSelect', root);
    var selectedUsersContainer = q('#selectedUsersContainer', root);
    if(!form || !questionBlock || !stickyStack) return;

    var toolbarMount = document.createElement('div');
    toolbarMount.className = 'phase3-toolbar-card';
    questionBlock.parentNode.insertBefore(toolbarMount, questionBlock);

    var flowMount = document.createElement('div');
    flowMount.className = 'phase3-card';
    stickyStack.appendChild(flowMount);

    var readinessMount = document.createElement('div');
    readinessMount.className = 'phase3-card';
    stickyStack.appendChild(readinessMount);

    function cards(){ return qa('.question-card', questionBlock); }
    function getSelectedUsers(){ return qa('.selected-user-chip input[name="target_values"]', selectedUsersContainer).map(function(el){ return el.value; }).filter(Boolean); }
    function readCard(card, index){
      var text = (q('textarea[name="question_text[]"]', card)?.value || '').trim();
      var type = q('select[name="question_type[]"]', card)?.value || 'text';
      var req = (q('select[name="question_required[]"]', card)?.value || '1') === '1';
      var options = (q('textarea[name="question_options[]"]', card)?.value || '').split('\n').map(function(x){ return x.trim(); }).filter(Boolean);
      var helper = (q('input[name="question_helper_text[]"]', card)?.value || '').trim();
      var logicMode = q('select[name="question_logic_mode[]"]', card)?.value || 'always';
      var logicSource = (q('input[name="question_logic_source[]"]', card)?.value || '').trim();
      var logicOperator = q('select[name="question_logic_operator[]"]', card)?.value || 'answered';
      var logicValue = (q('input[name="question_logic_value[]"]', card)?.value || '').trim();
      return {index:index+1, text:text, type:type, required:req, options:options, helper:helper, logicMode:logicMode, logicSource:logicSource, logicOperator:logicOperator, logicValue:logicValue};
    }
    function logicLabel(item){
      if(item.logicMode !== 'conditional') return 'Her zaman görünür';
      var op = ({answered:'yanıtlandıysa',selected_option:'seçenek eşitse',equals:'değer eşitse',contains:'içeriyorsa',gte:'>=',lte:'<='})[item.logicOperator] || 'koşul';
      return 'S' + (item.logicSource || '?') + ' ' + op + (item.logicValue ? (' • ' + item.logicValue) : '');
    }
    function cardErrors(item, total){
      var errors = [];
      if(!item.text) errors.push('Soru metni eksik.');
      if((item.type === 'single_choice' || item.type === 'multiple_choice') && item.options.length < 2) errors.push('Seçimli soruda en az iki seçenek gerekli.');
      if(item.logicMode === 'conditional'){
        var src = Number(item.logicSource || 0);
        if(!Number.isInteger(src) || src <= 0) errors.push('Koşul kaynağı geçerli değil.');
        else if(src >= item.index) errors.push('Koşul kaynağı yalnızca önceki sorulardan biri olabilir.');
        else if(src > total) errors.push('Koşul kaynağı mevcut soru sayısını aşıyor.');
        if(item.logicOperator !== 'answered' && !item.logicValue) errors.push('Koşul değeri eksik.');
      }
      return errors;
    }
    function ensureLogicBuilder(card){
      if(!card || card.dataset.phase3LogicBound === '1') return;
      card.dataset.phase3LogicBound = '1';
      var modeSelect = q('select[name="question_logic_mode[]"]', card);
      var sourceInput = q('input[name="question_logic_source[]"]', card);
      var operatorSelect = q('select[name="question_logic_operator[]"]', card);
      var valueInput = q('input[name="question_logic_value[]"]', card);
      var valueField = valueInput ? valueInput.closest('.field') : null;
      if(!modeSelect || !sourceInput || !operatorSelect || !valueInput || !valueField) return;
      var builder = document.createElement('div');
      builder.className = 'phase3-logic-builder';
      builder.innerHTML = ''
        + '<div class="phase3-logic-row">'
        +   '<div><label class="phase2-subtle">Koşulu kolay seç</label><select class="phase2-mini-select phase3-logic-source-select"><option value="">Önceki soru seçin</option></select></div>'
        +   '<div><label class="phase2-subtle">Hazır kural</label><div class="phase3-logic-presets">'
        +      '<button type="button" class="phase2-chip-btn" data-phase3-preset="answered">Yanıtlandıysa</button>'
        +      '<button type="button" class="phase2-chip-btn" data-phase3-preset="yes">Evet ise</button>'
        +      '<button type="button" class="phase2-chip-btn" data-phase3-preset="no">Hayır ise</button>'
        +      '<button type="button" class="phase2-chip-btn" data-phase3-preset="lte2"><= 2 ise</button>'
        +      '<button type="button" class="phase2-chip-btn" data-phase3-preset="gte4">>= 4 ise</button>'
        +   '</div></div>'
        + '</div>'
        + '<div class="phase3-logic-hint">Bu alan, mevcut koşul verisini daha rahat yönetmek için eklenmiştir. Arkadaki gerçek form alanları aynen korunur.</div>'
        + '<div class="phase3-logic-summary"></div>';
      valueField.insertAdjacentElement('afterend', builder);

      var sourceSelect = q('.phase3-logic-source-select', builder);
      var summary = q('.phase3-logic-summary', builder);
      function refreshSourceOptions(){
        var currentIndex = cards().indexOf(card) + 1;
        var rows = cards().slice(0, Math.max(0, currentIndex - 1)).map(function(item, idx){
          var data = readCard(item, idx);
          return '<option value="' + data.index + '"' + (String(data.index) === String(sourceInput.value || '') ? ' selected' : '') + '>S' + data.index + ' · ' + esc((data.text || typeLabel(data.type)).slice(0, 48)) + '</option>';
        });
        sourceSelect.innerHTML = '<option value="">Önceki soru seçin</option>' + rows.join('');
      }
      function refreshSummary(){
        var item = readCard(card, cards().indexOf(card));
        summary.innerHTML = '<span class="phase3-badge"><i class="fa-solid fa-eye"></i>' + esc(logicLabel(item)) + '</span>';
      }
      sourceSelect.addEventListener('change', function(){
        sourceInput.value = sourceSelect.value;
        if(sourceSelect.value && modeSelect.value !== 'conditional'){
          modeSelect.value = 'conditional';
          modeSelect.dispatchEvent(new Event('change', {bubbles:true}));
        }
        sourceInput.dispatchEvent(new Event('input', {bubbles:true}));
        refreshSummary();
      });
      qa('[data-phase3-preset]', builder).forEach(function(btn){
        btn.addEventListener('click', function(){
          var currentIndex = cards().indexOf(card) + 1;
          var fallbackSource = String(Math.max(1, currentIndex - 1));
          if(!sourceInput.value && currentIndex > 1){ sourceInput.value = fallbackSource; }
          modeSelect.value = 'conditional';
          var preset = btn.getAttribute('data-phase3-preset');
          if(preset === 'answered'){ operatorSelect.value = 'answered'; valueInput.value = ''; }
          if(preset === 'yes'){ operatorSelect.value = 'selected_option'; valueInput.value = 'Evet'; }
          if(preset === 'no'){ operatorSelect.value = 'selected_option'; valueInput.value = 'Hayır'; }
          if(preset === 'lte2'){ operatorSelect.value = 'lte'; valueInput.value = '2'; }
          if(preset === 'gte4'){ operatorSelect.value = 'gte'; valueInput.value = '4'; }
          sourceSelect.value = sourceInput.value;
          [modeSelect, sourceInput, operatorSelect, valueInput].forEach(function(el){ el.dispatchEvent(new Event('change', {bubbles:true})); el.dispatchEvent(new Event('input', {bubbles:true})); });
          refreshSummary();
          refreshAll();
        });
      });
      [modeSelect, sourceInput, operatorSelect, valueInput].forEach(function(el){
        el.addEventListener('change', function(){ refreshSourceOptions(); refreshSummary(); refreshAll(); });
        el.addEventListener('input', function(){ refreshSourceOptions(); refreshSummary(); refreshAll(); });
      });
      refreshSourceOptions();
      refreshSummary();
    }

    function renderToolbar(){
      var list = cards().map(readCard);
      var conditionalCount = list.filter(function(x){ return x.logicMode === 'conditional'; }).length;
      var requiredCount = list.filter(function(x){ return x.required; }).length;
      var invalidCount = list.reduce(function(sum, item){ return sum + (cardErrors(item, list.length).length ? 1 : 0); }, 0);
      toolbarMount.innerHTML = ''
        + '<div class="phase3-toolbar-head">'
        +   '<div><h4>Faz 3 · Akış ve davranış katmanı</h4><p>Bu katmanda builder yalnızca güzel görünmez; sorular arası akış, taslak/yayın hazırlığı ve toplu düzenleme davranışı da kazanır.</p></div>'
        +   '<div class="phase3-toolbar-actions">'
        +      '<button type="button" class="phase3-btn" data-phase3-action="all-required"><i class="fa-solid fa-asterisk"></i>Tümünü zorunlu yap</button>'
        +      '<button type="button" class="phase3-btn" data-phase3-action="all-optional"><i class="fa-regular fa-circle"></i>Tümünü isteğe bağlı yap</button>'
        +      '<button type="button" class="phase3-btn" data-phase3-action="clear-logic"><i class="fa-solid fa-broom"></i>Mantıkları temizle</button>'
        +      '<button type="button" class="phase3-btn" data-phase3-action="set-draft"><i class="fa-regular fa-file-lines"></i>Taslak moduna al</button>'
        +      '<button type="button" class="phase3-btn primary" data-phase3-action="set-published"><i class="fa-solid fa-bullhorn"></i>Yayın hazırlığı</button>'
        +      '<button type="button" class="phase3-btn" data-phase3-action="analyze"><i class="fa-solid fa-stethoscope"></i>Akışı tara</button>'
        +   '</div>'
        + '</div>'
        + '<div class="phase3-toolbar-stats">'
        +    '<span class="phase3-chip"><i class="fa-solid fa-list-check"></i><strong>' + list.length + '</strong> soru</span>'
        +    '<span class="phase3-chip"><i class="fa-solid fa-eye"></i><strong>' + conditionalCount + '</strong> koşullu</span>'
        +    '<span class="phase3-chip"><i class="fa-solid fa-asterisk"></i><strong>' + requiredCount + '</strong> zorunlu</span>'
        +    '<span class="phase3-chip"><i class="fa-solid fa-triangle-exclamation"></i><strong>' + invalidCount + '</strong> uyarı</span>'
        + '</div>';
      qa('[data-phase3-action]', toolbarMount).forEach(function(btn){
        btn.addEventListener('click', function(){ handleAction(btn.getAttribute('data-phase3-action')); });
      });
    }

    function renderFlow(){
      var list = cards().map(readCard);
      var items = list.map(function(item){
        var errs = cardErrors(item, list.length);
        return '<div class="phase3-flow-item" data-phase3-focus="' + item.index + '">'
          + '<div class="phase3-flow-top"><strong>S' + item.index + ' · ' + esc((item.text || typeLabel(item.type)).slice(0, 64)) + '</strong><span class="phase3-badge">' + esc(typeLabel(item.type)) + '</span></div>'
          + '<div class="phase3-flow-meta">'
          +   '<span class="phase3-badge"><i class="fa-solid fa-asterisk"></i>' + (item.required ? 'Zorunlu' : 'İsteğe bağlı') + '</span>'
          +   '<span class="phase3-badge"><i class="fa-solid fa-diagram-project"></i>' + esc(logicLabel(item)) + '</span>'
          +   (item.options.length ? '<span class="phase3-badge"><i class="fa-solid fa-list"></i>' + item.options.length + ' seçenek</span>' : '')
          + '</div>'
          + (errs.length ? '<div class="phase3-flow-line"><i class="fa-solid fa-triangle-exclamation"></i> ' + esc(errs[0]) + '</div>' : '<div class="phase3-flow-line">Soruda kritik akış uyarısı yok.</div>')
          + '</div>';
      }).join('');
      flowMount.innerHTML = ''
        + '<div class="phase3-card-head"><div><h4>Soru akış haritası</h4><p>Sağ panel artık sadece özet vermiyor; koşullu soruların zincirini de okunur hale getiriyor.</p></div></div>'
        + '<div class="phase3-list">' + (items || '<div class="phase3-empty">Henüz soru yok.</div>') + '</div>';
      qa('[data-phase3-focus]', flowMount).forEach(function(el){
        el.addEventListener('click', function(){
          var index = Number(el.getAttribute('data-phase3-focus') || '0');
          var card = cards()[index - 1];
          if(!card) return;
          card.classList.add('phase3-card-focus');
          setTimeout(function(){ card.classList.remove('phase3-card-focus'); }, 1500);
          card.scrollIntoView({behavior:'smooth', block:'center'});
        });
      });
    }

    function targetOk(){
      var mode = targetType ? (targetType.value || 'all') : 'all';
      if(mode === 'all') return true;
      if(mode === 'role') return !!(targetRoleSelect && targetRoleSelect.selectedOptions && targetRoleSelect.selectedOptions.length);
      if(mode === 'unit') return !!(targetUnitSelect && targetUnitSelect.selectedOptions && targetUnitSelect.selectedOptions.length);
      if(mode === 'user') return getSelectedUsers().length > 0;
      return false;
    }
    function renderReadiness(){
      var list = cards().map(readCard);
      var questionOk = list.length > 0 && list.every(function(item){ return !cardErrors(item, list.length).length; });
      var titleOk = !!(titleInput && titleInput.value.trim());
      var targetReady = targetOk();
      var dateReady = !startAtInput || !endAtInput || !startAtInput.value || !endAtInput.value || endAtInput.value >= startAtInput.value;
      var statusLabel = statusSelect ? ((statusSelect.value || 'draft') === 'published' ? 'Yayına ayarlı' : 'Taslakta') : 'Bilinmiyor';
      readinessMount.innerHTML = ''
        + '<div class="phase3-card-head"><div><h4>Yayın hazırlığı</h4><p>Faz 3 ile status alanı artık daha görünür yönetiliyor. Bu panel gerçek kaydı değiştirmez; sadece formdaki değeri yönlendirir.</p></div><span class="phase3-badge">' + esc(statusLabel) + '</span></div>'
        + '<div class="phase3-readiness-grid">'
        +   '<div class="phase3-kv ' + (titleOk ? 'ok' : 'bad') + '"><span>Başlık</span><strong>' + (titleOk ? 'Hazır' : 'Eksik') + '</strong></div>'
        +   '<div class="phase3-kv ' + (questionOk ? 'ok' : 'bad') + '"><span>Sorular</span><strong>' + (questionOk ? 'Akış temiz' : 'Kontrol gerekli') + '</strong></div>'
        +   '<div class="phase3-kv ' + (targetReady ? 'ok' : 'warn') + '"><span>Hedefleme</span><strong>' + (targetReady ? 'Tanımlı' : 'Eksik / genel') + '</strong></div>'
        +   '<div class="phase3-kv ' + (dateReady ? 'ok' : 'bad') + '"><span>Tarih aralığı</span><strong>' + (dateReady ? 'Uygun' : 'Başlangıç-bitiş hatalı') + '</strong></div>'
        + '</div>'
        + '<div class="phase3-toolbar-actions" style="margin-top:12px;">'
        +   '<button type="button" class="phase3-btn" data-phase3-action="set-draft"><i class="fa-regular fa-file-lines"></i>Taslakta bırak</button>'
        +   '<button type="button" class="phase3-btn primary" data-phase3-action="set-published"><i class="fa-solid fa-paper-plane"></i>Formu yayın moduna al</button>'
        + '</div>';
      qa('[data-phase3-action]', readinessMount).forEach(function(btn){ btn.addEventListener('click', function(){ handleAction(btn.getAttribute('data-phase3-action')); }); });
    }

    function markInvalid(){
      var list = cards().map(readCard);
      cards().forEach(function(card, idx){
        card.classList.toggle('phase3-invalid', cardErrors(list[idx], list.length).length > 0);
      });
    }

    function handleAction(action){
      if(action === 'all-required' || action === 'all-optional'){
        qa('select[name="question_required[]"]', questionBlock).forEach(function(sel){ sel.value = action === 'all-required' ? '1' : '0'; sel.dispatchEvent(new Event('change', {bubbles:true})); });
      }
      if(action === 'clear-logic'){
        qa('select[name="question_logic_mode[]"]', questionBlock).forEach(function(sel){ sel.value = 'always'; sel.dispatchEvent(new Event('change', {bubbles:true})); });
        qa('input[name="question_logic_source[]"]', questionBlock).forEach(function(inp){ inp.value = ''; inp.dispatchEvent(new Event('input', {bubbles:true})); });
        qa('select[name="question_logic_operator[]"]', questionBlock).forEach(function(sel){ sel.value = 'answered'; sel.dispatchEvent(new Event('change', {bubbles:true})); });
        qa('input[name="question_logic_value[]"]', questionBlock).forEach(function(inp){ inp.value = ''; inp.dispatchEvent(new Event('input', {bubbles:true})); });
      }
      if(action === 'set-draft' && statusSelect){ statusSelect.value = 'draft'; statusSelect.dispatchEvent(new Event('change', {bubbles:true})); }
      if(action === 'set-published' && statusSelect){ statusSelect.value = 'published'; statusSelect.dispatchEvent(new Event('change', {bubbles:true})); }
      if(action === 'analyze'){
        markInvalid();
        var firstInvalid = q('.question-card.phase3-invalid', questionBlock);
        if(firstInvalid) firstInvalid.scrollIntoView({behavior:'smooth', block:'center'});
      }
      refreshAll();
    }

    function refreshAll(){
      cards().forEach(ensureLogicBuilder);
      renderToolbar();
      renderFlow();
      renderReadiness();
      markInvalid();
    }

    var observer = new MutationObserver(function(){ window.requestAnimationFrame(refreshAll); });
    observer.observe(questionBlock, {childList:true, subtree:true});
    [titleInput, startAtInput, endAtInput, statusSelect, targetType, targetRoleSelect, targetUnitSelect].forEach(function(el){ if(el){ el.addEventListener('input', refreshAll); el.addEventListener('change', refreshAll); } });
    if(selectedUsersContainer){ selectedUsersContainer.addEventListener('click', function(){ setTimeout(refreshAll, 20); }); }
    qa('textarea, input, select', form).forEach(function(el){ el.addEventListener('input', function(){ window.requestAnimationFrame(refreshAll); }); el.addEventListener('change', function(){ window.requestAnimationFrame(refreshAll); }); });
    refreshAll();
  });
})();
