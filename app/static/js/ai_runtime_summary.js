(function () {
  const labelMap = {
    action_count: 'Faaliyet',
    delayed_count: 'Geciken',
    delayed_action_count: 'Geciken faaliyet',
    risky_count: 'Risk notu',
    goal_count: 'Hedef',
    meeting_count: 'Toplantı',
    progress_percent: 'İlerleme %',
    indicator_count: 'Gösterge',
    participant_count: 'Katılımcı',
    participant_limit: 'Kontenjan',
    media_count: 'Görsel',
    showcase_status: 'Vitrin durumu',
    visibility_level: 'Görünürlük',
    risk_note_present: 'Risk notu',
    chapter_count: 'Bölüm',
    progress_row_count: 'İzleme kaydı',
    average_progress_percent: 'Ort. ilerleme %',
    quiz_required: 'Quiz zorunlu',
    certificate_enabled: 'Sertifika',
    reaction_count: 'Tepki',
    comment_count: 'Yorum',
    attachment_count: 'Ek',
    image_count: 'Görsel ek',
    video_count: 'Video ek',
    file_count: 'Dosya ek',
    document_type_guess: 'Belge türü önerisi',
    folder_guess: 'Klasör önerisi',
    version_no: 'Sürüm',
    file_extension: 'Uzantı',
    file_size: 'Boyut',
    document_count: 'Belge',
    album_count: 'Albüm',
    orphan_document_count: 'Klasörsüz belge',
    draft_album_count: 'Taslak albüm',
    post_count: 'Paylaşım',
    pending_approval_count: 'Onay bekleyen',
    locked_post_count: 'Yoruma kapalı',
    certificate_ready_count: 'Sertifika uygun',
    completed_count: 'Tamamlanan',
    attendance_missing_count: 'Eksik yoklama',
    average_completion_rate: 'Ort. tamamlama %',
    participant_limit: 'Kontenjan'
  };

  function labelize(key) {
    if (labelMap[key]) return labelMap[key];
    return String(key || '')
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (m) => m.toUpperCase());
  }

  function createMetric(label, value) {
    const item = document.createElement('div');
    item.className = 'ai-runtime-metric';
    const title = document.createElement('div');
    title.className = 'ai-runtime-metric-label';
    title.textContent = label;
    const body = document.createElement('div');
    body.className = 'ai-runtime-metric-value';
    body.textContent = value == null || value === '' ? '-' : String(value);
    item.append(title, body);
    return item;
  }

  function pushBullet(target, text) {
    if (!text) return;
    const li = document.createElement('li');
    li.innerHTML = '<i class="fa-solid fa-circle"></i><span></span>';
    li.querySelector('span').textContent = String(text);
    target.appendChild(li);
  }

  function buildItems(data) {
    const items = [];
    const risks = Array.isArray(data.risks) ? data.risks : [];
    const notes = Array.isArray(data.notes) ? data.notes : [];
    const tags = Array.isArray(data.suggested_tags) ? data.suggested_tags : [];
    risks.forEach((row) => items.push('Risk: ' + row));
    notes.forEach((row) => items.push(row));
    if (data.fallback_rules) {
      const fallback = data.fallback_rules;
      (Array.isArray(fallback.risks) ? fallback.risks : []).forEach((row) => items.push('Kural denetimi: ' + row));
      (Array.isArray(fallback.notes) ? fallback.notes : []).forEach((row) => items.push(row));
    }
    if (tags.length) {
      items.push('Önerilen etiketler: ' + tags.join(', '));
    }
    if (Array.isArray(data.recommendation_ids) && data.recommendation_ids.length) {
      items.push('Açılan öneri kaydı: ' + data.recommendation_ids.length);
    }
    return items;
  }

  function renderPayload(card, data) {
    const stateEl = card.querySelector('[data-ai-state]');
    const summaryEl = card.querySelector('[data-ai-summary]');
    const metricsEl = card.querySelector('[data-ai-metrics]');
    const listEl = card.querySelector('[data-ai-list]');
    const feedbackEl = card.querySelector('[data-ai-feedback]');
    const feedbackResultEl = card.querySelector('[data-ai-feedback-result]');

    stateEl.hidden = true;
    stateEl.classList.remove('is-error');
    summaryEl.hidden = false;
    summaryEl.textContent = data.summary || (data.fallback_rules && data.fallback_rules.summary) || 'AI çıktısı üretildi.';

    metricsEl.innerHTML = '';
    const metrics = data.metrics && typeof data.metrics === 'object' ? data.metrics : null;
    if (metrics && Object.keys(metrics).length) {
      Object.entries(metrics).forEach(([key, value]) => {
        metricsEl.appendChild(createMetric(labelize(key), value));
      });
      metricsEl.hidden = false;
    } else {
      metricsEl.hidden = true;
    }

    listEl.innerHTML = '';
    const items = buildItems(data);
    if (items.length) {
      items.forEach((row) => pushBullet(listEl, row));
      listEl.hidden = false;
    } else {
      listEl.hidden = true;
    }

    const logId = data.ai_request_log_id;
    card.dispatchEvent(new CustomEvent('ai:rendered', { detail: { data } }));
    card.dataset.aiRequestLogId = logId ? String(logId) : '';
    if (logId) {
      feedbackEl.classList.add('visible');
      feedbackResultEl.textContent = '';
    } else {
      feedbackEl.classList.remove('visible');
      feedbackResultEl.textContent = '';
    }
  }

  async function postFeedback(card, type) {
    const requestLogId = card.dataset.aiRequestLogId;
    if (!requestLogId) return;
    const feedbackTemplate = card.dataset.feedbackUrlTemplate || '';
    const csrfToken = card.dataset.csrfToken || '';
    const targetUrl = feedbackTemplate.replace(/0\/?$/, requestLogId);
    const resultEl = card.querySelector('[data-ai-feedback-result]');
    resultEl.textContent = 'Kaydediliyor...';
    try {
      const response = await fetch(targetUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
          'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin',
        body: JSON.stringify({ feedback_type: type })
      });
      const payload = await response.json();
      if (!response.ok || !payload.ok) {
        throw new Error(payload.error || 'Geri bildirim kaydedilemedi.');
      }
      resultEl.textContent = type === 'helpful' ? 'Teşekkürler, faydalı olarak kaydedildi.' : 'Not alındı, geliştirme geri bildirimi işlendi.';
    } catch (error) {
      resultEl.textContent = error.message || 'Geri bildirim kaydedilemedi.';
    }
  }

  async function runRequest(card, mode) {
    const button = card.querySelector(`[data-ai-run="${mode}"]`);
    const stateEl = card.querySelector('[data-ai-state]');
    const summaryEl = card.querySelector('[data-ai-summary]');
    const metricsEl = card.querySelector('[data-ai-metrics]');
    const listEl = card.querySelector('[data-ai-list]');
    const feedbackEl = card.querySelector('[data-ai-feedback]');
    const url = mode === 'secondary' ? card.dataset.secondaryUrl : card.dataset.summaryUrl;
    if (!url) return;

    card.dataset.aiRequestLogId = '';
    feedbackEl.classList.remove('visible');
    stateEl.hidden = false;
    stateEl.classList.remove('is-error');
    stateEl.textContent = 'AI çıktısı hazırlanıyor...';
    summaryEl.hidden = true;
    metricsEl.hidden = true;
    listEl.hidden = true;
    button.disabled = true;

    try {
      const response = await fetch(url, {
        method: 'GET',
        credentials: 'same-origin',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
      const payload = await response.json();
      if (!response.ok || !payload.ok) {
        throw new Error(payload.error || 'AI çağrısı başarısız oldu.');
      }
      renderPayload(card, payload.data || {});
    } catch (error) {
      stateEl.hidden = false;
      stateEl.classList.add('is-error');
      stateEl.textContent = error.message || 'AI çağrısı başarısız oldu.';
      summaryEl.hidden = true;
      metricsEl.hidden = true;
      listEl.hidden = true;
    } finally {
      button.disabled = false;
    }
  }

  function initCard(card) {
    card.querySelectorAll('[data-ai-run]').forEach((button) => {
      button.addEventListener('click', () => runRequest(card, button.dataset.aiRun));
    });
    card.querySelectorAll('[data-ai-feedback-type]').forEach((button) => {
      button.addEventListener('click', () => postFeedback(card, button.dataset.aiFeedbackType));
    });
  }

  function boot() {
    document.querySelectorAll('.ai-runtime-card').forEach(initCard);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot, { once: true });
  } else {
    boot();
  }
})();
