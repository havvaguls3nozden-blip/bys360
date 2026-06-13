document.addEventListener('DOMContentLoaded', function () {
  const counters = document.querySelectorAll('[data-countup]');
  counters.forEach((node) => {
    const raw = String(node.textContent || '').trim();
    const target = Number(raw.replace(/[^0-9.-]/g, ''));
    if (!Number.isFinite(target)) return;
    const duration = 700;
    const start = performance.now();
    const animate = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      node.textContent = Math.round(target * eased).toLocaleString('tr-TR');
      if (progress < 1) requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  });
});
