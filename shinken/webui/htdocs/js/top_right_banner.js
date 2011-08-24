window.addEvent('domready', function(){
	
	var top_right = $('top_right_banner');
	if (top_right != null){

	    var fx = new Fx.Tween(top_right, {property: 'opacity'});
	    fx.start(0).chain(
			      //Notice that "this" refers to the calling object (in this case, the myFx object).
			      function(){ fx.start(1); },
			      function(){ fx.start(0); },
			      function(){ fx.start(1); },
			      function(){ fx.start(0); },
			      function(){ fx.start(1); },
			      function(){ fx.start(0); },
			      function(){ fx.start(1); }
			      ); //Will fade the Element out and in twice.
	}
    });




/* And make clouds animate */
window.addEvent("domready",function() {
	//settings
	var duration = 40000;
	var length = 2000;
	var count = 0;
  
	var tweener;
  
	// Executes the standard tween on the background position
	var run = function() {
	    tweener.tween("background-position","-" + (++count * length) + "px 0px");
	};
  
	// Defines the tween
	tweener = $("animate-area").setStyle("background-position","0px 0px").set("tween",{ 
		duration: duration, 
		transition: Fx.Transitions.linear,
		onComplete: run,
		link: "cancel"
	    });
  
	// Starts the initial run of the transition
	run();  
    });