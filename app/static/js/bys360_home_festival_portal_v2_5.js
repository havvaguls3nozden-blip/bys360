// BYS360_HOME_FESTIVAL_PORTAL_V2_5_1_BEGIN
(function(){
  function ready(fn){ if(document.readyState !== 'loading'){ fn(); } else { document.addEventListener('DOMContentLoaded', fn); } }
  ready(function(){
    document.querySelectorAll('.home-v251-showcase-card, .home-v251-feed-row, .home-v251-pill').forEach(function(card, index){
      card.style.setProperty('--v251-delay', (index * 28) + 'ms');
      card.classList.add('v251-ready');
    });
  });
})();
// BYS360_HOME_FESTIVAL_PORTAL_V2_5_1_END
