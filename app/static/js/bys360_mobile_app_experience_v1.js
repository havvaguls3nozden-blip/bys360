/* BYS360_MOBILE_APP_EXPERIENCE_V1 */
(function(){
  'use strict';
  var MOBILE_LIMIT = 900;
  function isMobile(){ return window.innerWidth <= MOBILE_LIMIT; }
  function setViewportClass(){
    document.body.classList.toggle('bys360-mobile-viewport', isMobile());
  }
  function wrapWideTables(){
    var tables = document.querySelectorAll('table:not([data-bys-mobile-ready])');
    tables.forEach(function(table){
      table.setAttribute('data-bys-mobile-ready','1');
      var isPerformance = /performance|performans|score|puan|karne|approval|onay|evaluation|degerlendirme/i.test(location.pathname + ' ' + table.className + ' ' + (table.closest('[class]') ? table.closest('[class]').className : ''));
      if(isPerformance){ table.classList.add('performance-mobile-card-table'); }
      var parent = table.parentElement;
      if(parent && !parent.classList.contains('table-responsive') && !parent.classList.contains('bys360-mobile-table-scroll')){
        var wrap = document.createElement('div');
        wrap.className = 'bys360-mobile-table-scroll';
        parent.insertBefore(wrap, table);
        wrap.appendChild(table);
      }
    });
  }
  function labelTableCells(){
    document.querySelectorAll('table').forEach(function(table){
      if(table.getAttribute('data-bys-mobile-labels') === '1') return;
      var headers = Array.prototype.map.call(table.querySelectorAll('thead th'), function(th){ return (th.textContent || '').trim(); });
      if(!headers.length) return;
      table.querySelectorAll('tbody tr').forEach(function(row){
        Array.prototype.forEach.call(row.children, function(cell, index){
          if(!cell.getAttribute('data-label') && headers[index]) cell.setAttribute('data-label', headers[index]);
        });
      });
      table.setAttribute('data-bys-mobile-labels','1');
    });
  }
  function enrichPerformanceForms(){
    var perfPath = /performance|performans|score|puan|karne|approval|onay|evaluation|degerlendirme/i.test(location.pathname);
    if(!perfPath) return;
    document.querySelectorAll('form').forEach(function(form){
      form.classList.add('bys360-mobile-performance-form');
      var submitZone = form.querySelector('.approval-actions,.score-submit-bar,.publish-actions,.sticky-actions,.form-actions');
      if(!submitZone){
        var buttons = form.querySelectorAll('button[type="submit"], input[type="submit"], .btn-primary, .btn-success, .btn-danger');
        if(buttons.length){
          var last = buttons[buttons.length-1];
          var container = last.closest('.row,.d-flex,.btn-group,.text-end,.text-center,.form-actions') || last.parentElement;
          if(container) container.classList.add('form-actions');
        }
      }
    });
    document.querySelectorAll('.rating-group,.puanlama-grubu,.score-inputs,.rating-options').forEach(function(group){
      group.classList.add('bys360-mobile-rating-ready');
    });
  }
  function init(){
    if(!document.body) return;
    setViewportClass();
    wrapWideTables();
    labelTableCells();
    enrichPerformanceForms();
  }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
  window.addEventListener('resize', function(){ window.clearTimeout(window.__bys360MobileResizeTimer); window.__bys360MobileResizeTimer=setTimeout(setViewportClass,120); }, {passive:true});
})();
