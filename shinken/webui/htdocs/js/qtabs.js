/**
 * QTabs for Mootools 1.11
 *
 * @version 1.0.0
 * @package qtabs
 * @author Massimo Giagnoni ( http://www.latenight-coding.com )
 * @copyright Copyright (C) 2008 Massimo Giagnoni. All rights reserved.
 * @license http://www.gnu.org/copyleft/gpl.html GNU/GPL
*/

var QTabs = new Class({
    options:{
		flexHeight:false,
		def_tab:0,
		autoplay:0,
		scrolling:0,
		delay:3000,
		duration:500,
		transition:'Quad',
		easing:'easeInOut',
		onActive: function(container, idx){
			var content = this.tcontents[idx];
			var s = container.getSize();
			var cw = s.size.x;
			if(this.options.flexHeight) {
				s = content.getSize();
				container.setStyle('height', s.size.y + 'px');
			}
					
			var d = (this.curTab >= 0 ? this.options.duration : 1);
			var sdir = this.options.scrolling;
			if(sdir == 'a') {
				if(idx > this.curTab) {
					sdir = 'lr';
				} else {
					sdir = 'rl';
				}	
			}
			var lft = [0,0];
			switch(sdir) {
				case 'lr':
					lft = [-cw,0];
					break;
				case 'rl':
					lft = [cw,0];
					break;
			}
	              
			this.fxOn = true;
			if(this.options.transition == 'linear') {
				var t = Fx.Transitions[this.options.transition];
			} else {
				var t = Fx.Transitions[this.options.transition][this.options.easing];
			}
			content.effects({
				duration: d,
				transition: t
			}).start({
				top: [0,0],
				left: lft,
				opacity: [1,1]
			});
			this.fxEnd.delay(d, this);
			this.tabs[idx].addClass('open').removeClass('closed');
		},

		onBackground: function(tab, content){
			content.setStyle('display', 'none');
			tab.addClass('closed').removeClass('open');
		}
    },

    initialize: function(m_id, options){
        
        this.setOptions(options);
        this.tabs = $('qtabs-'+ m_id).getElements('li')
        this.container = $('current-'+ m_id);
        this.tcontents = this.container.getElements('div.qtcontent');
		
		for (var i = 0, l = this.tabs.length; i < l; i++){
            var tab = this.tabs[i];
            tab.addEvent('click', this.display.bind(this, i));
            tab.addEvent('mouseenter', this.mouseEnter.bind(this, i));
            tab.addEvent('mouseleave', this.mouseLeave.bind(this, i));
        }
		this.curTab = -1;
		this.display(this.options.def_tab);

    },

    display: function(i){
    	if(i < 0 || i >= this.tabs.length) { i=0; }
        if(this.curTab == i || this.fxOn) {return;}
        
        $clear(this.timer);
        for (var c = 0, l = this.tabs.length; c < l; c++){
            if (c != i) {
            	this.tabs[c].addClass('closed').removeClass('open');
            } 
            this.tcontents[c].setOpacity(0);
        }
        this.fireEvent('onActive', [this.container, i]);
        this.curTab = i;
    },
    mouseEnter: function(i){
    	this.tabs[i].addClass('hover');
    },
    mouseLeave: function(i){
    	this.tabs[i].removeClass('hover');
    },
    fxEnd: function() {
		this.fxOn = false;
		if(this.options.autoplay) {
			var i = this.curTab + 1;
			if(i >= this.tcontents.length) {
				i = 0;
			}
			this.timer = this.display.delay(this.options.delay, this, i);
		}
	}
});

QTabs.implement(new Events);
QTabs.implement(new Options);