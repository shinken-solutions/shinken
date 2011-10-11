var SL_Slider = new Class({

	//implements
	Implements: [Options],	
	
	//variables setup
	numNav: new Array(),		    //will store number nav elements (if used)
	timer: null,					//periodical function variable holder
	isSliding: 0,					//flag for animation/click prevention
	direction: 1,					//flag for direction (forward/reverse)
	
	//options
	options: {
	slideTimer: 8000,  			    //Time between slides (1 second = 1000), a.k.a. the interval duration
	orientation: 'horizontal',      //vertical, horizontal, or none: None will create a fading in/out transition.
	fade: false,                    //if true will fade the outgoing slide - only used if orientation is != None
	isPaused: false,				//flag for paused state
	transitionTime: 1100, 		    //Transition time (1 second = 1000)
	transitionType: 'cubic:out',	//Transition type
	container: null,				//container element
	items:  null, 					//Array of elements for sliding
	itemNum: 0,						//Current item number
	numNavActive: false,			//Whether or not the number navigation will be used
	numNavHolder: null,			    //Element that holds the number navigation
	playBtn: null,					//Play (and pause) button element
	prevBtn: null,					//Previous button element
	nextBtn: null					//Next button element
	},

	//initialization
	initialize: function(options) {
		var self = this;
		
		//set options
		this.setOptions(options);
		
		//remove any scrollbar(s) on the container
		self.options.container.setStyle('overflow', "hidden");  
		
		//if there is a play/pause button, set up functionality for it
		if(self.options.playBtn != null) {
			//self.pauseIt();  
			self.options.playBtn.set('text', 'pause');
			
			self.options.playBtn.addEvents({
				'click': function() {
					self.pauseIt();
				},				
				'mouseenter' : function() {
					this.setStyle('cursor', 'pointer');
				},
				'mouseleave' : function() {
					
				}
			});
		}
		
		//if there is a prev & next button, set up functionality for them
		if(self.options.prevBtn && self.options.nextBtn){
			
			self.options.prevBtn.addEvents({ 
				'click' : function() {
					if(self.isSliding == 0){
						if(self.options.isPaused == false){
							$clear(self.timer);
							self.timer = self.slideIt.periodical(self.options.slideTimer, self, null);
						}
						self.direction = 0;
						self.slideIt();
					}
				},
				'mouseenter' : function() {
					this.setStyle('cursor', 'pointer');
				},
				'mouseleave' : function() {
				
				}
			});	
			
			this.options.nextBtn.addEvents({ 
				'click' : function() {
					if(self.isSliding == 0){
						if(self.options.isPaused == false){
							$clear(self.timer);
							self.timer = self.slideIt.periodical(self.options.slideTimer, self, null);
						}
						self.direction = 1;
						self.slideIt();
					}
				},
				'mouseenter' : function() {
					this.setStyle('cursor', 'pointer');
				},
				'mouseleave' : function() {
					
				}
			});	
		}
		
		//setup items (a.k.a. slides) from list
		self.options.items.each(function(el, i){
			  
			//f.y.i.  el = the element, i = the index
			el.setStyle('position', "absolute");
			var itemH = el.getSize().y;
			var itemW = el.getSize().x;
			if(self.options.orientation == 'vertical'){ 
                el.setStyle('top', (-1 * itemH));
                el.setStyle('left', 0);
            }else if(self.options.orientation == 'none') {
                el.setStyle('left', 0);
                el.setStyle('top', 0);
                el.set('opacity', 0);
			}else{
                el.setStyle('left', (-1 * itemW));
            }
			// -- Number nav setup
			if(self.options.numNavActive == true){
				//create numbered navigation boxes, and insert into the 'num_nav' ul)
				var numItem = new Element('li', {id: 'num'+i});
				var numLink = new Element('a', {
					'class': 'numbtn',
					'html': (i+1)
				});
				numItem.adopt(numLink);
				self.options.numNavHolder.adopt(numItem);
				self.numNav.push(numLink);
				numLink.set('morph', {duration: 100, transition: Fx.Transitions.linear, link: 'ignore'});
				
				numLink.addEvents({
					'click' : function(){
						self.numPress(i);
					},
					'mouseenter' : function() {
						this.setStyle('cursor', 'pointer');
					}
				});
				
				//set initial number to active state
				if(i == self.options.itemNum){
					var initNum = self.numNav[i];
					initNum.addClass('active');
				}
			}
			//end if num nav 'active'
		
		 });
	
	},

	//startup method
	start: function() {
		
		var self = this;
		
		self.slideIt(self.options.itemNum);  //initialize first slide
		
		if(self.options.isPaused == false){
			self.timer = self.slideIt.periodical(self.options.slideTimer, self, null);
			if(self.options.playBtn) self.options.playBtn.set('text', 'pause');
		}
		else{
			//self.pauseIt();
			if(self.options.playBtn) self.options.playBtn.set('text', 'play');
		}
		
	},
	
	
	slideIt: function(passedID) {
		
		var self = this;
		
		//get item to slide out
		var curItem = self.options.items[self.options.itemNum]; 
		if(self.options.numNavActive == true){
			var curNumItem =  self.numNav[self.options.itemNum];
		}
		
		//check for passedID presence
		if(passedID != null) {
			if(self.options.itemNum != passedID){
				if(self.options.itemNum > passedID) { 
					self.direction = 0; 
				} else { 
					self.direction = 1;
				}
				self.options.itemNum = passedID;
			}
		}
		else{
			self.changeIndex();	
		}
		
		
		//now get item to slide in using new index
		var newItem = self.options.items[self.options.itemNum];
		if(self.direction == 0){
			var curX = self.options.container.getSize().x;
			var newX = (-1 * newItem.getSize().x);
            var curY = self.options.container.getSize().y;
            var newY = (-1 * newItem.getSize().y);
		}
		else{
			var curX = (-1 * self.options.container.getSize().x);	
			var newX = newItem.getSize().x;
            var curY = (-1 * self.options.container.getSize().y);
            var newY = newItem.getSize().y;
		}
		
		
		//add/remove active number's highlight
		if(self.options.numNavActive == true){
			var newNumItem =  self.numNav[self.options.itemNum];
			newNumItem.addClass('active');
		}
		
		
		//set up our animation stylings
		var item_in = new Fx.Morph(newItem, {
		     duration: self.options.transitionTime, 
		     transition: self.options.transitionType,
		     link: 'ignore',
		     
		     onStart: function(){
				self.isSliding = 1;  //prevents extra clicks
			},
		     
		     onComplete: function(){
				self.isSliding = 0;  //prevents extra clicks
			}
		     
		});
		
		
		
        if(self.options.orientation == 'vertical'){
            if(self.options.fade == true){item_in.start({'opacity':[0,1],'top' : [newY, 0]});}
            else{item_in.start({'top' : [newY, 0]});}
        }else if(self.options.orientation == 'none') {
            item_in.start({'opacity':[0,1]});
        }else{
            if(self.options.fade == true){item_in.start({'opacity':[0,1],'left' : [newX, 0]});}
            else{item_in.start({'left' : [newX, 0]});}
        }
        
		
		if(curItem != newItem){
			var item_out = new Fx.Morph(curItem, {
				     duration: self.options.transitionTime, 
				     transition: self.options.transitionType,
				     link: 'ignore'
			});
			
			if(self.options.numNavActive == true){
				curNumItem.removeClass('active');
			}
			
            if(self.options.orientation == 'vertical'){
                if(self.options.fade == true){item_out.start({'opacity':[0],'top' : [(curY)]});}
                else{item_out.start({'top' : [(curY)]});}
            }else if(self.options.orientation == 'none') {
                item_out.start({'opacity':[1,0]});
            }else{
                if(self.options.fade == true){item_out.start({'opacity':[0],'left' : [(curX)]});}
                else{item_out.start({'left' : [(curX)]});}
            }
		}
	},
	
	
	//--------------------------------------------------------------------------------------------------------
	//supplementary functions  (mini-functions)
	//--------------------------------------------------------------------------------------------------------
	pauseIt: function () {
		
		var self = this;
		
		//only move if not currently moving
		if(self.isSliding == 0){
			if(self.options.isPaused == false){
				self.options.isPaused = true;
				$clear(self.timer);
				self.options.playBtn.set('text', 'play');				
			}
			else{
				self.options.isPaused = false;
				self.slideIt();
				self.timer = self.slideIt.periodical(self.options.slideTimer, this, null); 
				self.options.playBtn.set('text', 'pause');
			}
			
		} //end if not sliding
		
	},
	
	changeIndex: function() {
		var self = this; 
		
		var numItems = self.options.items.length;  //get number of slider items
		
		//change index based on value of 'direction' parameter
		if(self.direction == 1){
			if(self.options.itemNum < (numItems - 1)){
				self.options.itemNum++; 
			}
			else{
				self.options.itemNum = 0;
			}
		}
		else if(self.direction == 0){
			if(self.options.itemNum > 0){
				self.options.itemNum--; 
			}
			else{
				self.options.itemNum = (numItems - 1);
			}
		}	
		
	},
	
	numPress: function (theIndex) {
		var self = this;
		
		if((self.isSliding == 0) && (self.options.itemNum != theIndex)){
			if(self.options.isPaused == false){
				$clear(self.timer);
				self.timer = self.slideIt.periodical(self.options.slideTimer, this, null);
			}
			self.slideIt(theIndex);
		}
	}
	//------------------------  end supp. functions -----------------------------------------//

});