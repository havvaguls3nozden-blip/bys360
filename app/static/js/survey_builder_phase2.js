
(function(){
  function q(sel, root){ return (root || document).querySelector(sel); }
  function qa(sel, root){ return Array.from((root || document).querySelectorAll(sel)); }
  function esc(value){ return String(value || '').replace(/[&<>"']/g, function(c){ return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c]; }); }
  function typeLabel(type){ return ({text:'Metin',single_choice:'Tek seçim',multiple_choice:'Çoklu seçim',rating_5:'1-5 puan',rating_10:'1-10 puan',yes_no:'Evet / Hayır'})[type] || 'Metin'; }
  function optionPreset(key){
    if (key === 'yesno') return 'Evet\nHayır';
    if (key === 'three') return 'Seçenek 1\nSeçenek 2\nSeçenek 3';
    if (key === 'likert5') return 'Kesinlikle katılmıyorum\nKatılmıyorum\nKararsızım\nKatılıyorum\nKesinlikle katılıyorum';
    if (key === 'memnuniyet') return 'Çok memnunum\nMemnunum\nKararsızım\nMemnun değilim\nHiç memnun değilim';
    return '';
  }
  function onReady(fn){ if(document.readyState === 'loading'){ document.addEventListener('DOMContentLoaded', fn, {once:true}); } else { fn(); } }

  function init(){
    var root = q('[data-survey-studio="1"]');
    if(!root || root.dataset.phase2StudioBound === '1') return;
    root.dataset.phase2StudioBound = '1';
    var questionBlock = q('#questionBlock', root);
    var stickyStack = q('.sticky-stack', root);
    if(!questionBlock || !stickyStack) return;

    var inspectorMount = document.createElement('div');
    inspectorMount.className = 'glass-card panel-card';
    inspectorMount.id = 'builderInspectorMount';
    stickyStack.insertBefore(inspectorMount, stickyStack.firstElementChild || null);

    var libraryMount = document.createElement('div');
    libraryMount.className = 'glass-card panel-card';
    libraryMount.id = 'builderLibraryMount';
    stickyStack.insertBefore(libraryMount, inspectorMount.nextElementSibling);

    var activeCard = null;
    var scheduled = false;

    function cards(){ return qa('.question-card', questionBlock); }
    function selectCard(card){
      activeCard = card || cards()[0] || null;
      cards().forEach(function(item){ item.classList.toggle('is-selected', item === activeCard); });
      renderInspector();
      refreshCardSummaries();
    }
    function readCard(card, index){
      var textEl = q('textarea[name="question_text[]"]', card);
      var typeEl = q('select[name="question_type[]"]', card);
      var reqEl = q('select[name="question_required[]"]', card);
      var optEl = q('textarea[name="question_options[]"]', card);
      var helpEl = q('[name="question_helper_text[]"]', card);
      var logicModeEl = q('[name="question_logic_mode[]"]', card);
      var logicSourceEl = q('[name="question_logic_source[]"]', card);
      var logicOperatorEl = q('[name="question_logic_operator[]"]', card);
      var logicValueEl = q('[name="question_logic_value[]"]', card);
      var options = (optEl && optEl.value || '').split('\n').map(function(x){ return x.trim(); }).filter(Boolean);
      return {
        index: (index || 0) + 1,
        title: (textEl && textEl.value || '').trim(),
        type: typeEl ? typeEl.value : 'text',
        required: reqEl ? reqEl.value === '1' : true,
        options: options,
        helper: (helpEl && helpEl.value || '').trim(),
        logicMode: logicModeEl ? logicModeEl.value : 'always',
        logicSource: (logicSourceEl && logicSourceEl.value || '').trim(),
        logicOperator: logicOperatorEl ? logicOperatorEl.value : 'answered',
        logicValue: (logicValueEl && logicValueEl.value || '').trim()
      };
    }
    function logicText(item){
      if(item.logicMode !== 'conditional') return 'Her zaman görünür';
      var op = ({answered:'yanıtlandıysa',selected_option:'seçenek eşitse',equals:'değer eşitse',contains:'içeriyorsa',gte:'>=',lte:'<='})[item.logicOperator] || 'koşul';
      return 'S' + (item.logicSource || '?') + ' ' + op + (item.logicValue ? (' • ' + item.logicValue) : '');
    }
    function ensureControls(card){
      if(!card || card.dataset.phase2Bound === '1') return;
      card.dataset.phase2Bound = '1';
      var head = q('.question-head', card);
      var tools = q('.question-tools', card);
      if(head && tools && !q('.phase2-tools', head)){
        var toolWrap = document.createElement('div');
        toolWrap.className = 'phase2-tools';
        toolWrap.innerHTML = ''
          + '<button type="button" class="phase2-icon-btn phase2-drag-handle" title="Sürükle"><i class="fa-solid fa-grip-vertical"></i></button>'
          + '<button type="button" class="phase2-icon-btn" data-action="move-up" title="Yukarı taşı"><i class="fa-solid fa-arrow-up"></i></button>'
          + '<button type="button" class="phase2-icon-btn" data-action="move-down" title="Aşağı taşı"><i class="fa-solid fa-arrow-down"></i></button>'
          + '<button type="button" class="phase2-icon-btn" data-action="duplicate" title="Çoğalt"><i class="fa-regular fa-copy"></i></button>'
          + '<button type="button" class="phase2-icon-btn" data-action="collapse" title="Daralt / genişlet"><i class="fa-solid fa-compress"></i></button>';
        head.insertBefore(toolWrap, tools);
      }
      if(!q('.phase2-card-summary', card)){
        var summary = document.createElement('div');
        summary.className = 'phase2-card-summary';
        head.insertAdjacentElement('afterend', summary);
      }
      var optionsField = q('.options-field', card);
      if(optionsField && !q('.phase2-option-presets', optionsField)){
        var label = q('label', optionsField);
        if(label){
          var wrap = document.createElement('div');
          wrap.className = 'phase2-field-head';
          label.parentNode.insertBefore(wrap, label);
          wrap.appendChild(label);
          var presets = document.createElement('div');
          presets.className = 'phase2-option-presets';
          presets.innerHTML = ''
            + '<button type="button" class="phase2-chip-btn" data-options-preset="three">3 seçenek</button>'
            + '<button type="button" class="phase2-chip-btn" data-options-preset="likert5">Likert 5</button>'
            + '<button type="button" class="phase2-chip-btn" data-options-preset="memnuniyet">Memnuniyet</button>';
          wrap.appendChild(presets);
        }
      }
      qa('[data-options-preset]', card).forEach(function(btn){
        if(btn.dataset.phase2PresetBound === '1') return;
        btn.dataset.phase2PresetBound = '1';
        btn.addEventListener('click', function(){
          var textarea = q('textarea[name="question_options[]"]', card);
          if(!textarea) return;
          textarea.value = optionPreset(btn.dataset.optionsPreset);
          textarea.dispatchEvent(new Event('input', {bubbles:true}));
        });
      });
      var collapseBtn = q('[data-action="collapse"]', card);
      if(collapseBtn && collapseBtn.dataset.phase2CollapseBound !== '1'){
        collapseBtn.dataset.phase2CollapseBound = '1';
        collapseBtn.addEventListener('click', function(){
          card.classList.toggle('is-collapsed');
          collapseBtn.classList.toggle('is-active', card.classList.contains('is-collapsed'));
          var icon = q('i', collapseBtn);
          if(icon) icon.className = card.classList.contains('is-collapsed') ? 'fa-solid fa-expand' : 'fa-solid fa-compress';
          refreshCardSummaries();
          renderInspector();
        });
      }
      card.addEventListener('click', function(evt){
        if(evt.target.closest('.phase2-option-presets')) return;
        selectCard(card);
      });
      qa('textarea, input, select', card).forEach(function(el){
        el.addEventListener('focus', function(){ selectCard(card); });
        el.addEventListener('input', queueRender);
        el.addEventListener('change', queueRender);
      });
    }
    function refreshCardSummaries(){
      cards().forEach(function(card, index){
        ensureControls(card);
        var summary = q('.phase2-card-summary', card);
        if(!summary) return;
        var item = readCard(card, index);
        summary.innerHTML = ''
          + '<span class="phase2-pill"><i class="fa-solid fa-font"></i>' + esc(typeLabel(item.type)) + '</span>'
          + '<span class="phase2-pill"><i class="fa-solid fa-asterisk"></i>' + (item.required ? 'Zorunlu' : 'İsteğe bağlı') + '</span>'
          + '<span class="phase2-pill"><i class="fa-solid fa-list"></i>' + (item.options.length ? item.options.length + ' seçenek' : 'Seçeneksiz') + '</span>'
          + '<span class="phase2-pill"><i class="fa-solid fa-eye"></i>' + esc(logicText(item)) + '</span>';
      });
    }
    function addQuestionByType(type){
      var addBtn = q('#addQuestionBtn', root);
      if(!addBtn || addBtn.disabled) return;
      var before = cards().length;
      addBtn.click();
      setTimeout(function(){
        var list = cards();
        var card = list[list.length - 1];
        if(!card || list.length < before) return;
        ensureControls(card);
        selectCard(card);
        var typeEl = q('select[name="question_type[]"]', card);
        var textEl = q('textarea[name="question_text[]"]', card);
        var optionsEl = q('textarea[name="question_options[]"]', card);
        if(typeEl){ typeEl.value = type; typeEl.dispatchEvent(new Event('change', {bubbles:true})); }
        if(textEl && !textEl.value.trim()) textEl.value = typeLabel(type) + ' sorusu';
        if(optionsEl && ['single_choice','multiple_choice'].indexOf(type) !== -1 && !optionsEl.value.trim()) optionsEl.value = optionPreset('three');
        if(optionsEl && type === 'yes_no' && !optionsEl.value.trim()) optionsEl.value = optionPreset('yesno');
        queueRender();
        card.scrollIntoView({behavior:'smooth', block:'center'});
      }, 20);
    }
    function renderLibrary(){
      libraryMount.innerHTML = ''
        + '<div class="phase2-inspector">'
        +   '<div class="phase2-inspector-head"><div><h4>Hızlı soru kütüphanesi</h4><p>İkinci katmanda en çok kullanılan soru türleri tek dokunuşla eklenir. Kart seçiliyse yeni soru onun altına gelir.</p></div></div>'
        +   '<div class="phase2-library">'
        +     '<div class="phase2-library-row">'
        +       '<button type="button" data-add-type="text"><i class="fa-solid fa-align-left"></i> Açık uçlu metin</button>'
        +       '<button type="button" data-add-type="single_choice"><i class="fa-regular fa-circle-dot"></i> Tek seçim</button>'
        +     '</div>'
        +     '<div class="phase2-library-row">'
        +       '<button type="button" data-add-type="multiple_choice"><i class="fa-regular fa-square-check"></i> Çoklu seçim</button>'
        +       '<button type="button" data-add-type="yes_no"><i class="fa-solid fa-toggle-on"></i> Evet / Hayır</button>'
        +     '</div>'
        +     '<div class="phase2-library-row">'
        +       '<button type="button" data-add-type="rating_5"><i class="fa-solid fa-star-half-stroke"></i> 1-5 puan</button>'
        +       '<button type="button" data-add-type="rating_10"><i class="fa-solid fa-ranking-star"></i> 1-10 puan</button>'
        +     '</div>'
        +   '</div>'
        + '</div>';
      qa('[data-add-type]', libraryMount).forEach(function(btn){ btn.addEventListener('click', function(){ addQuestionByType(btn.dataset.addType); }); });
    }
    function buildWarnings(item){
      var warnings = [];
      if(!item.title) warnings.push('Soru başlığı boş. Kaydetmede bu kart hata üretir.');
      if(['single_choice','multiple_choice'].indexOf(item.type) !== -1 && item.options.length < 2) warnings.push('Seçimli sorularda en az iki seçenek olmalıdır.');
      if(item.logicMode === 'conditional' && !item.logicSource) warnings.push('Koşullu görünürlük açık ama kaynak soru numarası boş.');
      if(item.logicMode === 'conditional' && item.logicOperator !== 'answered' && !item.logicValue) warnings.push('Seçilen koşul operatörü için koşul değeri girilmelidir.');
      return warnings;
    }
    function renderInspector(){
      var card = activeCard || cards()[0] || null;
      if(!card){
        inspectorMount.innerHTML = '<div class="phase2-empty">Henüz aktif soru yok. Sol taraftan soru ekleyerek stüdyoyu başlatabilirsiniz.</div>';
        return;
      }
      var index = cards().indexOf(card);
      var item = readCard(card, index);
      var warnings = buildWarnings(item);
      inspectorMount.innerHTML = ''
        + '<div class="phase2-inspector">'
        +   '<div class="phase2-inspector-card">'
        +     '<div class="phase2-inspector-head">'
        +       '<div><h4>Alan ayarları • Soru ' + (index + 1) + '</h4><p>Seçili kartın temel tür, yardım, zorunluluk ve koşul ayarlarını bu panelden yönetebilirsiniz.</p></div>'
        +       '<span class="phase2-pill">' + esc(typeLabel(item.type)) + '</span>'
        +     '</div>'
        +     '<div class="phase2-inspector-grid">'
        +       '<div class="full"><label class="phase2-subtle">Başlık</label><textarea class="phase2-mini-textarea" id="phase2InspectorTitle">' + esc(item.title) + '</textarea></div>'
        +       '<div><label class="phase2-subtle">Tür</label><select class="phase2-mini-select" id="phase2InspectorType">'
        +         '<option value="text"' + (item.type==='text'?' selected':'') + '>Metin</option>'
        +         '<option value="single_choice"' + (item.type==='single_choice'?' selected':'') + '>Tek seçim</option>'
        +         '<option value="multiple_choice"' + (item.type==='multiple_choice'?' selected':'') + '>Çoklu seçim</option>'
        +         '<option value="rating_5"' + (item.type==='rating_5'?' selected':'') + '>1-5 puan</option>'
        +         '<option value="rating_10"' + (item.type==='rating_10'?' selected':'') + '>1-10 puan</option>'
        +         '<option value="yes_no"' + (item.type==='yes_no'?' selected':'') + '>Evet / Hayır</option>'
        +       '</select></div>'
        +       '<div><label class="phase2-subtle">Zorunluluk</label><select class="phase2-mini-select" id="phase2InspectorRequired"><option value="1"' + (item.required?' selected':'') + '>Zorunlu</option><option value="0"' + (!item.required?' selected':'') + '>İsteğe bağlı</option></select></div>'
        +       '<div class="full"><label class="phase2-subtle">Yardım metni</label><input class="phase2-mini-input" id="phase2InspectorHelper" value="' + esc(item.helper) + '" placeholder="Katılımcıya kısa yönlendirme"></div>'
        +       '<div><label class="phase2-subtle">Görünürlük</label><select class="phase2-mini-select" id="phase2InspectorLogicMode"><option value="always"' + (item.logicMode==='always'?' selected':'') + '>Her zaman</option><option value="conditional"' + (item.logicMode==='conditional'?' selected':'') + '>Koşullu</option></select></div>'
        +       '<div><label class="phase2-subtle">Koşul kaynağı</label><input class="phase2-mini-input" id="phase2InspectorLogicSource" value="' + esc(item.logicSource) + '" placeholder="Örn: 2"></div>'
        +       '<div><label class="phase2-subtle">Operatör</label><select class="phase2-mini-select" id="phase2InspectorLogicOperator">'
        +         '<option value="answered"' + (item.logicOperator==='answered'?' selected':'') + '>Yanıtlandıysa</option>'
        +         '<option value="selected_option"' + (item.logicOperator==='selected_option'?' selected':'') + '>Seçenek eşitse</option>'
        +         '<option value="equals"' + (item.logicOperator==='equals'?' selected':'') + '>Değer eşitse</option>'
        +         '<option value="contains"' + (item.logicOperator==='contains'?' selected':'') + '>İçeriyorsa</option>'
        +         '<option value="gte"' + (item.logicOperator==='gte'?' selected':'') + '>>=</option>'
        +         '<option value="lte"' + (item.logicOperator==='lte'?' selected':'') + '><=</option>'
        +       '</select></div>'
        +       '<div><label class="phase2-subtle">Koşul değeri</label><input class="phase2-mini-input" id="phase2InspectorLogicValue" value="' + esc(item.logicValue) + '" placeholder="Örn: Evet veya 4"></div>'
        +     '</div>'
        +   '</div>'
        +   '<div class="phase2-inspector-card">'
        +     '<div class="phase2-inspector-head"><div><h4>Kısa kalite kontrolü</h4><p>Kaydetmeden önce bu karta ait riskleri görün. Bu katman backend doğrulamasını kaldırmaz; seni önden uyarır.</p></div></div>'
        +     '<div class="phase2-warning-list">' + (warnings.length ? warnings.map(function(w){ return '<div class="phase2-warning">' + esc(w) + '</div>'; }).join('') : '<div class="phase2-kv"><span>Durum</span><strong>Bu kart şu an temiz görünüyor</strong></div>') + '</div>'
        +   '</div>'
        +   '<div class="phase2-inspector-card">'
        +     '<div class="phase2-inspector-head"><div><h4>Katılımcı ön tadım</h4><p>Seçili sorunun yalın hali burada görünür. Bu, genel önizlemeden bağımsız küçük bir mikrogörünümdür.</p></div></div>'
        +     '<div class="phase2-preview-box"><strong>' + esc(item.title || ('Soru ' + (index + 1))) + '</strong><span>' + esc(item.helper || 'Yardım metni yok. Katılımcı bu soruyu doğrudan görür.') + '</span><div class="phase2-inline-actions" style="margin-top:10px;">' + (item.options.length ? item.options.slice(0,5).map(function(opt){ return '<span class="phase2-pill">' + esc(opt) + '</span>'; }).join('') : '<span class="phase2-pill">' + esc(typeLabel(item.type)) + '</span>') + '</div><div class="phase2-subtle" style="margin-top:10px;">' + esc(logicText(item)) + '</div></div>'
        +   '</div>'
        + '</div>';

      function bindMirror(id, selector, prop){
        var source = q(id, inspectorMount);
        var target = q(selector, card);
        if(!source || !target) return;
        var evtName = (target.tagName === 'SELECT') ? 'change' : 'input';
        source.addEventListener(evtName, function(){
          target.value = source.value;
          target.dispatchEvent(new Event(evtName, {bubbles:true}));
          queueRender();
        });
        source.addEventListener('input', function(){
          target.value = source.value;
          target.dispatchEvent(new Event('input', {bubbles:true}));
          queueRender();
        });
      }
      bindMirror('#phase2InspectorTitle', 'textarea[name="question_text[]"]');
      bindMirror('#phase2InspectorType', 'select[name="question_type[]"]');
      bindMirror('#phase2InspectorRequired', 'select[name="question_required[]"]');
      bindMirror('#phase2InspectorHelper', '[name="question_helper_text[]"]');
      bindMirror('#phase2InspectorLogicMode', '[name="question_logic_mode[]"]');
      bindMirror('#phase2InspectorLogicSource', '[name="question_logic_source[]"]');
      bindMirror('#phase2InspectorLogicOperator', '[name="question_logic_operator[]"]');
      bindMirror('#phase2InspectorLogicValue', '[name="question_logic_value[]"]');
    }
    function queueRender(){ if(scheduled) return; scheduled = true; requestAnimationFrame(function(){ scheduled = false; refreshCardSummaries(); renderInspector(); }); }
    function bindExisting(){ cards().forEach(ensureControls); if(!activeCard) activeCard = cards()[0] || null; selectCard(activeCard); }

    questionBlock.addEventListener('click', function(evt){
      var card = evt.target.closest('.question-card');
      if(card) selectCard(card);
    });
    questionBlock.addEventListener('focusin', function(evt){
      var card = evt.target.closest('.question-card');
      if(card) selectCard(card);
    });
    var observer = new MutationObserver(function(mutations){
      mutations.forEach(function(m){
        Array.from(m.addedNodes || []).forEach(function(node){
          if(node.nodeType === 1 && node.classList.contains('question-card')) ensureControls(node);
          if(node.nodeType === 1) qa('.question-card', node).forEach(ensureControls);
        });
      });
      bindExisting();
      queueRender();
    });
    observer.observe(questionBlock, {childList:true, subtree:false});
    renderLibrary();
    bindExisting();
    queueRender();
  }

  onReady(init);
})();
