(function () {
  const root = document.getElementById('publication-local-spread-root');
  if (!root) return;

  const pageCount = Number(root.dataset.pageCount || 0);
  const pageTemplate = root.dataset.pageTemplate || '';
  const storageKey = root.dataset.storageKey || ('publication-local-spread-' + Date.now());
  const rendererAvailable = String(root.dataset.rendererAvailable || 'false') === 'true';

  const loading = root.querySelector('[data-role="loading"]');
  const fallback = root.querySelector('[data-role="fallback"]');
  const stage = root.querySelector('[data-role="stage"]');
  const thumbs = root.querySelector('[data-role="thumbs"]');
  const pageLabel = root.querySelector('[data-role="page-label"]');
  const modeLabel = root.querySelector('[data-role="mode-label"]');
  const jumpInput = root.querySelector('[data-role="jump-input"]');
  const prevBtn = root.querySelector('[data-action="prev"]');
  const nextBtn = root.querySelector('[data-action="next"]');
  const singleBtn = root.querySelector('[data-action="single"]');
  const spreadBtn = root.querySelector('[data-action="spread"]');
  const fullscreenBtn = root.querySelector('[data-action="fullscreen"]');

  if (!rendererAvailable || !pageCount || !pageTemplate) {
    if (loading) loading.hidden = true;
    if (fallback) fallback.hidden = false;
    return;
  }

  function buildSpreads(totalPages) {
    const spreads = [];
    if (!totalPages || totalPages < 1) return spreads;
    spreads.push([1, null]);
    for (let page = 2; page <= totalPages; page += 2) {
      spreads.push([page, page + 1 <= totalPages ? page + 1 : null]);
    }
    return spreads;
  }

  const spreads = buildSpreads(pageCount);
  let mode = window.innerWidth < 992 ? 'single' : 'spread';
  let index = 0;

  try {
    const saved = JSON.parse(localStorage.getItem(storageKey) || '{}');
    if (saved.mode === 'single' || saved.mode === 'spread') mode = saved.mode;
    if (typeof saved.index === 'number' && saved.index >= 0 && saved.index < spreads.length) index = saved.index;
  } catch (_) {}

  function persist() {
    try {
      localStorage.setItem(storageKey, JSON.stringify({ mode, index }));
    } catch (_) {}
  }

  function goPrev() {
    if (index <= 0) return;
    index -= 1;
    persist();
    draw();
  }

  function goNext() {
    if (index >= spreads.length - 1) return;
    index += 1;
    persist();
    draw();
  }

  function pageUrl(pageNo, width) {
    const replaced = pageTemplate.replace('__PAGE__', String(pageNo));
    const joiner = replaced.includes('?') ? '&' : '?';
    return replaced + joiner + 'w=' + encodeURIComponent(width || 1400);
  }

  function create(tag, cls, text) {
    const el = document.createElement(tag);
    if (cls) el.className = cls;
    if (text != null) el.textContent = text;
    return el;
  }

  function updateToolbar() {
    if (pageLabel) {
      const pair = spreads[index] || [1, null];
      pageLabel.textContent = mode === 'spread'
        ? (pair[1] ? (pair[0] + '–' + pair[1]) : String(pair[0]))
        : String(pair[0]);
    }
    if (modeLabel) modeLabel.textContent = mode === 'spread' ? 'Çift Sayfa' : 'Tek Sayfa';
    if (singleBtn) singleBtn.classList.toggle('primary', mode === 'single');
    if (spreadBtn) spreadBtn.classList.toggle('primary', mode === 'spread');
    if (prevBtn) prevBtn.disabled = index <= 0;
    if (nextBtn) nextBtn.disabled = index >= spreads.length - 1;
  }

  function renderThumbs() {
    if (!thumbs) return;
    thumbs.innerHTML = '';
    spreads.forEach((pair, spreadIndex) => {
      const btn = create('button', 'pub-thumb' + (spreadIndex === index ? ' is-active' : ''));
      btn.type = 'button';
      btn.addEventListener('click', () => {
        index = spreadIndex;
        persist();
        draw();
      });

      const preview = create('div', 'pub-thumb-preview' + (mode === 'single' ? ' single' : ''));
      const left = create('img', 'pub-thumb-page');
      left.loading = 'lazy';
      left.alt = 'Sayfa ' + pair[0];
      left.src = pageUrl(pair[0], 220);
      preview.appendChild(left);

      if (mode === 'spread') {
        if (pair[1]) {
          const right = create('img', 'pub-thumb-page');
          right.loading = 'lazy';
          right.alt = 'Sayfa ' + pair[1];
          right.src = pageUrl(pair[1], 220);
          preview.appendChild(right);
        } else {
          preview.appendChild(create('div', 'pub-thumb-page pub-thumb-page--blank', 'Boş'));
        }
      }

      btn.appendChild(preview);
      btn.appendChild(create('span', 'pub-thumb-label', pair[1] ? (pair[0] + '–' + pair[1]) : String(pair[0])));
      thumbs.appendChild(btn);
    });
  }

  function renderPageSurface(pageNo, side, width) {
    const surface = create('button', 'pub-page-sheet' + (side ? ' is-' + side : ''));
    surface.type = 'button';
    surface.dataset.side = side || '';
    if (!pageNo) {
      surface.classList.add('blank-sheet');
      surface.setAttribute('aria-label', 'Boş sayfa');
      surface.appendChild(create('div', 'pub-page-blank', 'Boş'));
      return surface;
    }
    surface.setAttribute('aria-label', 'Sayfa ' + pageNo);
    const meta = create('div', 'pub-page-meta', 'Sayfa ' + pageNo);
    const img = create('img', 'pub-page-image');
    img.loading = 'eager';
    img.alt = 'Sayfa ' + pageNo;
    img.src = pageUrl(pageNo, width);
    surface.appendChild(meta);
    surface.appendChild(img);
    return surface;
  }

  function bindStageClicks(frame) {
    if (!frame) return;

    frame.addEventListener('click', (event) => {
      const pageSurface = event.target.closest('.pub-page-sheet');
      if (!pageSurface) return;

      const rect = frame.getBoundingClientRect();
      const offsetX = event.clientX - rect.left;
      const ratio = rect.width > 0 ? (offsetX / rect.width) : 0.5;

      if (mode === 'spread') {
        if (pageSurface.dataset.side === 'left' || ratio < 0.5) {
          goPrev();
        } else {
          goNext();
        }
        return;
      }

      if (ratio < 0.35) {
        goPrev();
      } else {
        goNext();
      }
    });
  }

  function draw() {
    if (!stage) return;
    const pair = spreads[index] || [1, null];
    stage.innerHTML = '';

    const frame = create('div', mode === 'spread' ? 'pub-spread-frame is-clickable' : 'pub-single-frame is-clickable');
    const stageWidth = Math.max(stage.clientWidth || 1200, 320);
    const targetWidth = mode === 'spread' ? Math.floor((stageWidth - 48) / 2) : Math.min(stageWidth - 32, 1400);

    frame.appendChild(renderPageSurface(pair[0], 'left', targetWidth));
    if (mode === 'spread') {
      frame.appendChild(renderPageSurface(pair[1], 'right', targetWidth));
    }

    stage.appendChild(frame);
    bindStageClicks(frame);
    updateToolbar();
    renderThumbs();
    if (jumpInput) jumpInput.value = String(pair[0] || 1);
    if (loading) loading.hidden = true;
  }

  prevBtn && prevBtn.addEventListener('click', goPrev);
  nextBtn && nextBtn.addEventListener('click', goNext);

  singleBtn && singleBtn.addEventListener('click', () => {
    mode = 'single';
    persist();
    draw();
  });

  spreadBtn && spreadBtn.addEventListener('click', () => {
    mode = 'spread';
    persist();
    draw();
  });

  jumpInput && jumpInput.addEventListener('change', () => {
    const page = Number(jumpInput.value || 0);
    if (!page) return;
    const targetIndex = spreads.findIndex((pair) => pair[0] === page || pair[1] === page);
    if (targetIndex >= 0) {
      index = targetIndex;
      persist();
      draw();
    }
  });

  fullscreenBtn && fullscreenBtn.addEventListener('click', async () => {
    try {
      if (!document.fullscreenElement) {
        await root.requestFullscreen();
      } else {
        await document.exitFullscreen();
      }
    } catch (_) {}
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowLeft') {
      event.preventDefault();
      goPrev();
    } else if (event.key === 'ArrowRight' || event.key === ' ') {
      event.preventDefault();
      goNext();
    }
  });

  window.addEventListener('resize', () => {
    if (window.innerWidth < 992 && mode !== 'single') mode = 'single';
    persist();
    draw();
  });

  draw();
})();
