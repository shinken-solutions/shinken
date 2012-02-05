/**
 * Description:
 * Example: <div class="pulsate"> <p> Example DIV </p> </div>
 */

$(function() {
  var p = $(".pulsate");
  for(var i=0; i<5; i++) {
    p.animate({opacity: 0.2}, 1000, 'linear')
     .animate({opacity: 1}, 1000, 'linear');
  }
});

/**
 * Description:
 * Example: <a rel="tooltip" href="#" data-original-title="Lorem Ipsum">Lorem Ipsum</a>
 */

$(function(){
    $('a[rel=tooltip]').tooltip();
});

/**
 * Description:
 * Example: <div class="quickinfo"> Lorem Ipsum </div>
 */

$(function(){
    $(".quickinfo").tooltip({placement: 'bottom'});
});