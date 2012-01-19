/*Copyright (C) 2009-2011 :
     Gabes Jean, naparuba@gmail.com
     Gerhard Lausser, Gerhard.Lausser@consol.de
     Gregory Starck, g.starck@gmail.com
     Hartmut Goebel, h.goebel@goebel-consult.de
     Andreas Karfusehr, andreas@karfusehr.de
 
 This file is part of Shinken.
 
 Shinken is free software: you can redistribute it and/or modify
 it under the terms of the GNU Affero General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.
 
 Shinken is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Affero General Public License for more details.
 
 You should have received a copy of the GNU Affero General Public License
 along with Shinken.  If not, see <http://www.gnu.org/licenses/>.
*/


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





/* This is the class that will manage a div with a background
that scrool from right to left */
bgScroller = new Class({
	Implements: [Events, Options],
	options: {
	    duration: 40000
	},
	tweener: null,
	length: 0,
	count: 0,
	verticalPosition: null,
	run: function() {
	    this.tweener.tween('background-position', ('-' + (++this.count * this.length) + 'px ' + this.verticalPosition));
	},
	initialize: function(element, options){
	    this.setOptions(options);
	    this.tweener = element;
	    this.length = this.tweener.getSize().x;
	    this.verticalPosition = this.tweener.getStyle("background-position").split(" ")[1];
	    this.tweener.setStyle("background-position", ("0px " + this.verticalPosition));
	    this.tweener.set('tween', {
		    duration: this.options.duration,
			transition: Fx.Transitions.linear,
			onComplete: this.run.bind(this),
			wait: false
			});
	    this.run();
	}
    });

/* And now we call it*/
window.addEvent("domready", function() {
	/* Maybe the page do not have sucgh aera, if so, we bail out :)*/
	var animate_area = $('animate-area');
	if (animate_area != null){

	    var frontScroller = new bgScroller($("animate-area"), { duration: 9000 });
	    var middleScroller = new bgScroller($("animate-area-back-1"), { duration: 15000 });
	    var backScroller = new bgScroller($("animate-area-back-2"), { duration: 12000 });
	}
    });