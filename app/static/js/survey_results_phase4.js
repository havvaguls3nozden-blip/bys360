
(function () {
  if (window.__bysSurveyResultsPhase4) return;
  window.__bysSurveyResultsPhase4 = true;

  function q(sel, root) { return (root || document).querySelector(sel); }
  function qa(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }
  function text(el) { return (el && el.textContent || '').replace(/\s+/g, ' ').trim(); }
  function esc(value) {
    return String(value || '').replace(/[&<>"']/g, function (c) {
      return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c];
    });
  }
  function csvEscape(v) {
    var s = String(v == null ? '' : v);
    if (/[",\n;]/.test(s)) return '"' + s.replace(/"/g, '""') + '"';
    return s;
  }
  function onReady(fn) {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fn, { once: true });
    else fn();
  }

  function normalizeMode(mode) {
    return ({ rating: 'Puan', options: 'Seçim', text: 'Metin' })[mode] || 'Diğer';
  }
  function badgeClass(mode) {
    return mode === 'rating' ? 'sr4-badge--rating' : mode === 'options' ? 'sr4-badge--options' : 'sr4-badge--text';
  }
  function priority(score, mode, count) {
    if (mode === 'rating') {
      if (score >= 80) return { label: 'Güçlü', cls: 'strong' };
      if (score >= 60) return { label: 'İzle', cls: 'watch' };
      return { label: 'Risk', cls: 'risk' };
    }
    if (mode === 'text') {
      return count >= 5 ? { label: 'İçerik var', cls: 'strong' } : { label: 'İzle', cls: 'watch' };
    }
    return count >= 10 ? { label: 'Yoğun', cls: 'strong' } : { label: 'İzle', cls: 'watch' };
  }

  onReady(function () {
    var shell = q('.results-shell');
    var filterMount = q('#surveyResultsFilterMount');
    var insightMount = q('#surveyResultsInsightMount');
    var tableMount = q('#surveyResultsTableMount');
    var cards = qa('.survey-result-card');
    if (!shell || !filterMount || !insightMount || !tableMount || !cards.length) return;

    var rows = cards.map(function (card, index) {
      var mode = card.dataset.mode || 'text';
      var title = text(q('.question-title', card));
      var helper = text(q('.question-sub', card));
      var count = parseFloat(card.dataset.count || '0') || 0;
      var score = parseFloat(card.dataset.score || '0') || 0;
      var topLabel = card.dataset.topLabel || '';
      var topPct = card.dataset.topPct || '';
      var insight = '';
      if (mode === 'rating') {
        var big = text(q('.question-big-score', card));
        var scale = card.dataset.scale || '';
        insight = big ? ('Ortalama ' + big + (scale ? '/' + scale : '')) : 'Henüz puan oluşmadı';
      } else if (mode === 'options') {
        insight = topLabel ? ('Baskın seçenek: ' + topLabel + (topPct ? ' (%' + topPct + ')' : '')) : 'Henüz seçim yoğunluğu oluşmadı';
      } else {
        insight = text(q('.text-answer', card)) || 'Metin örneği henüz oluşmadı';
        if (insight.length > 120) insight = insight.slice(0, 117) + '...';
      }
      return {
        id: 'sr4row' + (index + 1),
        index: index + 1,
        mode: mode,
        modeLabel: normalizeMode(mode),
        title: title,
        helper: helper,
        count: count,
        score: score,
        priority: priority(score, mode, count),
        insight: insight,
        card: card
      };
    });

    filterMount.innerHTML = ''
      + '<div class="sr4-shell">'
      + '  <div class="sr4-card">'
      + '    <div class="sr4-card-body">'
      + '      <div class="sr4-toolbar">'
      + '        <div><h3 class="sr4-title">Yanıt çalışma masası</h3><p class="sr4-sub">Soru sonuçlarını tablo gibi tarayın, riskli başlıkları filtreleyin ve görünür tabloyu tek tıkla dışa aktarın.</p></div>'
      + '        <div class="sr4-actions">'
      + '          <button type="button" class="sr4-link-btn" data-sr4-action="export-visible"><i class="fa-solid fa-file-arrow-down"></i> Görünür tabloyu indir</button>'
      + '          <button type="button" class="sr4-link-btn" data-sr4-action="reset"><i class="fa-solid fa-rotate-left"></i> Filtreleri sıfırla</button>'
      + '        </div>'
      + '      </div>'
      + '      <div class="sr4-filter-grid">'
      + '        <div class="sr4-field"><label>Arama</label><div class="sr4-search"><i class="fa-solid fa-magnifying-glass"></i><input id="sr4Search" type="search" placeholder="Soru başlığı veya içgörü ara"></div></div>'
      + '        <div class="sr4-field"><label>Tür</label><select id="sr4Mode"><option value="all">Tümü</option><option value="rating">Puan</option><option value="options">Seçim</option><option value="text">Metin</option></select></div>'
      + '        <div class="sr4-field"><label>Sırala</label><select id="sr4Sort"><option value="index">Doğal sıra</option><option value="count_desc">Kayıt sayısı (çoktan aza)</option><option value="score_asc">Puan (düşükten yükseğe)</option><option value="score_desc">Puan (yüksekten düşüğe)</option><option value="title">Başlığa göre</option></select></div>'
      + '        <div class="sr4-field"><label>Durum filtresi</label><select id="sr4Priority"><option value="all">Tümü</option><option value="risk">Risk</option><option value="watch">İzle</option><option value="strong">Güçlü</option></select></div>'
      + '      </div>'
      + '      <div class="sr4-chip-row" style="margin-top:14px;">'
      + '        <button type="button" class="sr4-chip is-active" data-mode-chip="all">Tüm sorular</button>'
      + '        <button type="button" class="sr4-chip" data-mode-chip="rating">Puanlı alanlar</button>'
      + '        <button type="button" class="sr4-chip" data-mode-chip="options">Seçimli alanlar</button>'
      + '        <button type="button" class="sr4-chip" data-mode-chip="text">Metin alanları</button>'
      + '      </div>'
      + '    </div>'
      + '  </div>'
      + '</div>';

    insightMount.innerHTML = '<div class="sr4-stats" id="sr4Stats"></div>';

    tableMount.innerHTML = ''
      + '<div class="sr4-card">'
      + '  <div class="sr4-card-body">'
      + '    <div class="sr4-toolbar">'
      + '      <div><h3 class="sr4-title">Filtreli soru tablosu</h3><p class="sr4-sub">Jotform Tables benzeri tarama hissi için görünür sorular aşağıda düz listeye çevrilir. Satırdan ilgili kart detayına atlayabilirsiniz.</p></div>'
      + '      <div class="sr4-inline-note"><i class="fa-solid fa-arrow-down-short-wide"></i><span id="sr4Counter">0 satır görünür</span></div>'
      + '    </div>'
      + '    <div class="sr4-table-wrap">'
      + '      <table class="sr4-table">'
      + '        <thead><tr><th>#</th><th>Soru</th><th>Tür</th><th>Kayıt</th><th>İçgörü</th><th>Durum</th><th>Detay</th></tr></thead>'
      + '        <tbody id="sr4TableBody"></tbody>'
      + '      </table>'
      + '    </div>'
      + '    <div id="sr4Empty" class="sr4-empty" style="display:none;margin-top:14px;">Filtreye uyan soru bulunamadı. Arama ve durum filtrelerini gevşetip tekrar deneyin.</div>'
      + '  </div>'
      + '</div>';

    var statsEl = q('#sr4Stats');
    var searchEl = q('#sr4Search');
    var modeEl = q('#sr4Mode');
    var sortEl = q('#sr4Sort');
    var priorityEl = q('#sr4Priority');
    var tableBody = q('#sr4TableBody');
    var counterEl = q('#sr4Counter');
    var emptyEl = q('#sr4Empty');

    function renderStats(visible) {
      var rating = visible.filter(function (x) { return x.mode === 'rating'; });
      var risk = visible.filter(function (x) { return x.priority.cls === 'risk'; });
      var dense = visible.slice().sort(function (a, b) { return b.count - a.count; })[0];
      var low = rating.slice().sort(function (a, b) { return a.score - b.score; })[0];
      statsEl.innerHTML = [
        { label: 'Görünür soru', value: visible.length, sub: 'Mevcut filtreye uyan toplam satır.' },
        { label: 'Riskli başlık', value: risk.length, sub: 'Düşük puanlı veya dikkat isteyen alan.' },
        { label: 'En yoğun kayıt', value: dense ? dense.count : 0, sub: dense ? dense.title : 'Kayıt yoğunluğu oluşmadı' },
        { label: 'En düşük puan', value: low ? ('%' + low.score) : '—', sub: low ? low.title : 'Puanlı alan görünmüyor' }
      ].map(function (item) {
        return '<div class="sr4-stat"><div class="sr4-stat-label">' + esc(item.label) + '</div><div class="sr4-stat-value">' + esc(item.value) + '</div><div class="sr4-stat-sub">' + esc(item.sub) + '</div></div>';
      }).join('');
    }

    function getVisibleRows() {
      var term = (searchEl.value || '').trim().toLowerCase();
      var mode = modeEl.value;
      var sort = sortEl.value;
      var pr = priorityEl.value;
      var visible = rows.filter(function (row) {
        var hitTerm = !term || row.title.toLowerCase().indexOf(term) !== -1 || row.insight.toLowerCase().indexOf(term) !== -1 || row.helper.toLowerCase().indexOf(term) !== -1;
        var hitMode = mode === 'all' || row.mode === mode;
        var hitPriority = pr === 'all' || row.priority.cls === pr;
        return hitTerm && hitMode && hitPriority;
      });
      visible.sort(function (a, b) {
        if (sort === 'count_desc') return b.count - a.count || a.index - b.index;
        if (sort === 'score_asc') return a.score - b.score || a.index - b.index;
        if (sort === 'score_desc') return b.score - a.score || a.index - b.index;
        if (sort === 'title') return a.title.localeCompare(b.title, 'tr');
        return a.index - b.index;
      });
      return visible;
    }

    function render() {
      var visible = getVisibleRows();
      rows.forEach(function (row) {
        row.card.classList.toggle('sr4-hidden-card', visible.indexOf(row) === -1);
      });
      renderStats(visible);
      counterEl.textContent = visible.length + ' satır görünür';
      emptyEl.style.display = visible.length ? 'none' : '';
      tableBody.innerHTML = visible.map(function (row) {
        return ''
          + '<tr>'
          +   '<td>' + row.index + '</td>'
          +   '<td class="sr4-col-question"><strong>' + esc(row.title) + '</strong><span>' + esc(row.helper || 'Ek açıklama yok') + '</span></td>'
          +   '<td><span class="sr4-badge ' + badgeClass(row.mode) + '">' + esc(row.modeLabel) + '</span></td>'
          +   '<td>' + esc(row.count) + '</td>'
          +   '<td>' + esc(row.insight) + '</td>'
          +   '<td><span class="sr4-priority sr4-priority--' + row.priority.cls + '">' + esc(row.priority.label) + '</span></td>'
          +   '<td><button type="button" class="sr4-link-btn" data-row="' + row.id + '"><i class="fa-solid fa-arrow-up-right-from-square"></i> Karta git</button></td>'
          + '</tr>';
      }).join('');
      qa('[data-row]', tableBody).forEach(function (btn) {
        btn.addEventListener('click', function () {
          var row = rows.find(function (item) { return item.id === btn.dataset.row; });
          if (!row) return;
          row.card.scrollIntoView({ behavior: 'smooth', block: 'center' });
          row.card.classList.add('sr4-hit');
          setTimeout(function () { row.card.classList.remove('sr4-hit'); }, 1200);
        });
      });
    }

    qa('[data-mode-chip]').forEach(function (chip) {
      chip.addEventListener('click', function () {
        qa('[data-mode-chip]').forEach(function (x) { x.classList.remove('is-active'); });
        chip.classList.add('is-active');
        modeEl.value = chip.dataset.modeChip;
        render();
      });
    });

    [searchEl, modeEl, sortEl, priorityEl].forEach(function (el) { el.addEventListener('input', render); el.addEventListener('change', render); });
    q('[data-sr4-action="reset"]').addEventListener('click', function () {
      searchEl.value = '';
      modeEl.value = 'all';
      sortEl.value = 'index';
      priorityEl.value = 'all';
      qa('[data-mode-chip]').forEach(function (x) { x.classList.toggle('is-active', x.dataset.modeChip === 'all'); });
      render();
    });
    q('[data-sr4-action="export-visible"]').addEventListener('click', function () {
      var visible = getVisibleRows();
      var lines = [['Sıra','Soru','Tür','Kayıt','İçgörü','Durum']].concat(visible.map(function (row) {
        return [row.index, row.title, row.modeLabel, row.count, row.insight, row.priority.label];
      }));
      var csv = lines.map(function (line) { return line.map(csvEscape).join(';'); }).join('\n');
      var blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      var link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = 'bys360_survey_results_faz4.csv';
      document.body.appendChild(link);
      link.click();
      setTimeout(function () { URL.revokeObjectURL(link.href); link.remove(); }, 0);
    });

    render();
  });
})();
