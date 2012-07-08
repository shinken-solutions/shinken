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

window.addEvent('domready',function(){
	(function($) {

	    this.IPhoneCheckboxes = new Class({

		    //implements
		    Implements: [Options],

		    //options
		    options: {
			checkedLabel: 'ON',
			uncheckedLabel: 'OFF',
			background: '#fff',
			containerClass: 'iPhoneCheckContainer',
			labelOnClass: 'iPhoneCheckLabelOn',
			labelOffClass: 'iPhoneCheckLabelOff',
			handleClass: 'iPhoneCheckHandle',
			handleBGClass: 'iPhoneCheckHandleBG',
			handleSliderClass: 'iPhoneCheckHandleSlider',
			elements: 'input[type=checkbox]'
		    },

		    //initialization
		    initialize: function(options) {
			//set options
			this.setOptions(options);
			//elements
			this.elements = $$(this.options.elements);
			//observe checkboxes
			this.elements.each(function(el) {
				this.observe(el);
			    },this);
		    },

		    //a method that does whatever you want
		    observe: function(el) {
			//turn off opacity
			el.set('opacity',0);
			//create wrapper div
			var wrap = new Element('div',{
				'class': this.options.containerClass
			    }).inject(el.getParent());
			//inject this checkbox into it
			el.inject(wrap);
			//now create subsquent divs and labels
			var handle = new Element('div',{'class':this.options.handleClass}).inject(wrap);
			var handlebg = new Element('div',{'class':this.options.handleBGClass,'style':this.options.background}).inject(handle);
			var handleSlider = new Element('div',{'class':this.options.handleSliderClass}).inject(handle);
			var offLabel = new Element('label',{'class':this.options.labelOffClass,text:this.options.uncheckedLabel}).inject(wrap);
			var onLabel = new Element('label',{'class':this.options.labelOnClass,text:this.options.checkedLabel}).inject(wrap);
			var rightSide = wrap.getSize().x - 39;

			//fx instances
			el.offFx = new Fx.Tween(offLabel,{'property':'opacity','duration':200});
			el.onFx = new Fx.Tween(onLabel,{'property':'opacity','duration':200});
			//mouseup / event listening
			wrap.addEvent('mouseup',function() {
				var is_onstate = !el.checked; //originally 0
				var new_left = (is_onstate ? rightSide : 0);
				var bg_left = (is_onstate ? 34 : 0);
				handlebg.hide();
				new Fx.Tween(handle,{
					duration: 100,
					    'property': 'left',
					    onComplete: function() {
					    handlebg.setStyle('left',bg_left).show();
					}
				}).start(new_left);
				//label animations
				if(is_onstate) {
				    el.offFx.start(0);
				    el.onFx.start(1);
				}
				else {
				    el.offFx.start(1);
				    el.onFx.start(0);
				}
				//set checked
				el.set('checked',is_onstate);
			    });
			//initial load
			if(el.checked){
			    offLabel.set('opacity',0);
			    onLabel.set('opacity',1);
			    handle.setStyle('left',rightSide);
			    handlebg.setStyle('left',34);
			} else {
			    onLabel.set('opacity',0);
			    handlebg.setStyle('left',0);
			}
		    }
		});

	})(document.id);

	/* usage */
	var chx = new IPhoneCheckboxes();
    });