$(function() {
  var p = $(".pulsate");
  for(var i=0; i<5; i++) {
    p.animate({opacity: 0.2}, 1000, 'linear')
     .animate({opacity: 1}, 1000, 'linear');
  }
});