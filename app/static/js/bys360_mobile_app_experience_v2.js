/* BYS360_MOBILE_APP_EXPERIENCE_V2
   Performans ekranları için mobil app davranış katmanı.
*/
(function(){
  'use strict';
  var MOBILE_LIMIT = 900;
  var PERF_RE = /performance|performans|score|puan|karne|approval|onay|evaluation|degerlendirme|president|baskan/i;
  function isMobile(){ return window.innerWidth <= MOBILE_LIMIT; }
  function txt(el){ return (el && el.textContent || '').replace(/\s+/g,' ').trim(); }
  function pageKind(){
    var p = location.pathname.toLowerCase();
    return {
      performance: PERF_RE.test(p),
      scoring: /score|puan|evaluation|degerlendirme|scoring/.test(p),
      scorecard: /scorecard|karne/.test(p),
      approval: /approval|onay|president|baskan/.test(p)
    };
  }
  function setBodyClasses(){
    var k = pageKind();
    document.body.classList.toggle('bys360-performance-mobile-v2', isMobile() && k.performance);
    document.body.classList.toggle('bys360-score-mobile-v2', isMobile() && k.scoring);
    document.body.classList.toggle('bys360-scorecard-mobile-v2', isMobile() && k.scorecard);
    document.body.classList.toggle('bys360-approval-mobile-v2', isMobile() && k.approval);
  }
  function labelTables(){
    if(!pageKind().performance) return;
    document.querySelectorAll('table:not([data-bys360-mobile-v2])').forEach(function(table){
      var headers = Array.prototype.map.call(table.querySelectorAll('thead th'), txt);
      var tableText = txt(table).toLowerCase();
      var shouldCard = /puan|score|karne|kriter|amir|onay|süreç|surec|geçmiş|gecmis|personel|değerlendirme|degerlendirme/.test(tableText + ' ' + table.className);
      if(shouldCard) table.classList.add('bys360-mobile-v2-card-table');
      if(headers.length){
        table.querySelectorAll('tbody tr').forEach(function(row){
          Array.prototype.forEach.call(row.children, function(cell, i){
            if(headers[i] && !cell.getAttribute('data-label')) cell.setAttribute('data-label', headers[i]);
          });
        });
      }
      table.setAttribute('data-bys360-mobile-v2','1');
    });
  }
  function markForms(){
    if(!pageKind().performance) return;
    document.querySelectorAll('form:not([data-bys360-mobile-v2])').forEach(function(form){
      form.classList.add('bys360-mobile-performance-form-v2');
      form.setAttribute('data-bys360-mobile-v2','1');
      var actionZone = form.querySelector('.approval-actions,.score-submit-bar,.publish-actions,.sticky-actions,.form-actions');
      if(!actionZone){
        var submitters = form.querySelectorAll('button[type="submit"], input[type="submit"], .btn-primary, .btn-success, .btn-danger, .btn-warning');
        if(submitters.length){
          var last = submitters[submitters.length-1];
          var host = last.closest('.row,.d-flex,.text-end,.text-center,.btn-group,.button-row') || last.parentElement;
          if(host) host.classList.add('bys360-mobile-actionbar-v2');
        }
      }
    });
  }
  function enhanceRatingGroups(){
    if(!pageKind().scoring) return;
    var selectors = '.score-inputs,.rating-group,.puanlama-grubu,.rating-options,[class*="score-options"],[class*="rating-options"]';
    document.querySelectorAll(selectors).forEach(function(group){
      group.classList.add('bys360-mobile-rating-strip-v2');
    });
    document.querySelectorAll('.criterion-row,.criteria-row,.evaluation-item,.scoring-item,.score-item').forEach(function(item){
      item.classList.add('bys360-mobile-score-item-v2');
      var title = item.querySelector('h1,h2,h3,h4,h5,strong,.title,.criterion-title,.criteria-title,.evaluation-title,.score-item-title');
      if(title) title.classList.add('bys360-mobile-score-title-v2');
      var help = item.querySelector('p,.text-muted,.criterion-desc,.criteria-desc,.evaluation-desc,.description');
      if(help) help.classList.add('bys360-mobile-score-help-v2');
    });
  }
  function buildSectionNav(){
    if(!pageKind().performance || document.querySelector('.bys360-mobile-section-nav-v2')) return;
    var candidates = Array.prototype.slice.call(document.querySelectorAll('h2,h3,.card-title,.section-title'))
      .filter(function(el){ return txt(el).length > 2 && txt(el).length < 48; })
      .slice(0,6);
    if(candidates.length < 2) return;
    var nav = document.createElement('nav');
    nav.className='bys360-mobile-section-nav-v2';
    candidates.forEach(function(el, i){
      if(!el.id) el.id='bys360-mob-v2-section-'+i;
      var a=document.createElement('a'); a.href='#'+el.id; a.textContent=txt(el); if(i===0) a.className='is-active';
      a.addEventListener('click',function(){ nav.querySelectorAll('a').forEach(function(x){x.classList.remove('is-active')}); a.classList.add('is-active'); });
      nav.appendChild(a);
    });
    var anchor = document.querySelector('.content-wrap main,.content-wrap,.container-fluid,.container,main') || document.body;
    anchor.insertBefore(nav, anchor.firstChild);
  }
  function init(){
    if(!document.body) return;
    setBodyClasses();
    if(!isMobile()) return;
    labelTables();
    markForms();
    enhanceRatingGroups();
    buildSectionNav();
  }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
  window.addEventListener('resize', function(){ window.clearTimeout(window.__bys360MobileV2Timer); window.__bys360MobileV2Timer=setTimeout(init,150); }, {passive:true});
})();
