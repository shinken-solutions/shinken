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
