/*
UvumiTools Dropdown Menu v1.1.2 http://uvumi.com/tools/dropdown.html

Copyright (c) 2009 Uvumi LLC

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
*/

var UvumiDropdown = new Class({
	Implements:Options,
	
	options:{
		clickToOpen:false,	//if set to true,  must click to open submenues
		openDelay:150,	//if hover mode, duration the mouse must stay on target before submenu is opened. if exits before delay expires, timer is cleared 
		closeDelay:500,	//delay before the submenu close when mouse exits. If mouse enter the submenu again before timer expires, it's cleared
		duration:250,	//duration in millisecond of opening/closing effect
		link:'cancel',
		transition:Fx.Transitions.linear,	//effect's transitions. See http://docs.mootools.net/Fx/Fx.Transitions for more details
		mode:'horizontal' //if set to horizontal, the top level menu will be displayed horizontally. If set to vertical, it will be displayed vertically. If it does not match any of those two words, 'horizontal' will be used.
	},

	initialize: function(menu,options){
		this.menu = menu;
		this.setOptions(options);
		if(this.options.mode != 'horizontal' && this.options.mode != 'vertical'){
			this.options.mode = 'horizontal';
		}
		//some versions of Safari and Chrome run domready before DOM is actually ready, causing wrong positioning. If you still have some display issues in those browser try to increase the delay value a bit. I tried to keep it as low as possible, but sometimes it can take a bit longer than expected
		if(Browser.Engine.webkit){
			window.addEvent('domready',this.domReady.delay(200,this));
		}else{
			window.addEvent('domready',this.domReady.bind(this));
		}
	},
	
	domReady:function(){
		this.menu = $(this.menu);
		if(!$defined(this.menu)){
			return false;
		}
		//if passed element is not a UL, tries to find one in the children elements
		if(this.menu.get('tag')!='ul'){
			this.menu = this.menu.getElement('ul');
			if(!$defined(this.menu)){
				return false;
			}
		}
		//handles pages written form right to left.
		if(this.menu.getStyle('direction') == 'rtl' || $(document.body).getStyle('direction') == 'rtl'){
			this.rtl = true;
			if(Browser.Engine.trident && $(document.body).getStyle('direction') == 'rtl'){
				this.menu.getParent().setStyle('direction','ltr');
				this.menu.setStyle('direction','rtl');
			}
		}
		//start setup
		this.menu.setStyles({
			visibility:'hidden',
			display:'block',
			overflow:'hidden',
			height:0,
			marginLeft:(Browser.Engine.trident?1:-1)
		});
		//we call the createSubmenu function on the main UL, which is a recursive function
		this.createSubmenu(this.menu);
		//the LIs must be floated to be displayed horisotally
		if(this.options.mode=='horizontal'){
			this.menu.getChildren('li').setStyles({
				'float':(this.rtl?'right':'left'),
				display:'block',
				top:0
			});
		
			//We create an extar LI which role will be to clear the floats of the others
			var clear = new Element('li',{
				html:"&nbsp;",
				styles:{
					clear:(this.rtl?'right':'left'),
					display:(Browser.Engine.trident?'inline':'block'), //took me forever to find that fix
					position:'relative',
					top:0,
					height:0,
					width:0,
					fontSize:0,
					lineHeight:0,
					margin:0,
					padding:0
				}
			}).inject(this.menu);
		}else{
			this.menu.getChildren('li').setStyles({
				display:'block',
				top:0
			});
		}
		this.menu.setStyles({
			height:'40px',
			overflow:'visible',
			visibility:'visible'
		});
		//hack for IE, again
		this.menu.getElements('a').setStyle('display',(Browser.Engine.trident?'inline-block':'block'));
	},
	
	createSubmenu:function(ul){
		//we collect all the LI of the ul
		var LIs = ul.getChildren('li');
		var offset = 0;
		//loop through the LIs
		LIs.each(function(li){
			li.setStyles({				
				position:'relative',
				display:'block',
				top:-offset,
				zIndex:1
			});
			offset += li.getSize().y;
			var innerUl = li.getFirst('ul');
			//if the current LI contains a UL
			if($defined(innerUl)){
				ul.getElements('ul').setStyle('display','none');
				//if the current UL is the main one, that means we are still in the top row, and the submenu must drop down
				if(ul == this.menu && this.options.mode == 'horizontal'){
					li.addClass('submenu-down');
					var x = 0;
					var y = li.getSize().y;
					this.options.link='cancel';
					li.store('animation',new Fx.Elements($$(innerUl,innerUl.getChildren('li')).setStyle('opacity',0),this.options));
				//if the current UL is not the main one, the sub menu must pop from the side
				}else{
					li.addClass('submenu-left');
					var x = li.getSize().x-(this.rtl&&!Browser.Engine.trident?2:1)*li.getStyle('border-left-width').toInt();
					var y = -li.getStyle('border-bottom-width').toInt();
					this.options.link='chain';
					li.store('animation',new Fx.Elements($$(innerUl,innerUl.getChildren('li')).setStyle('opacity',0),this.options));
					offset=li.getSize().y+li.getPosition(this.menu).y;
				}
				innerUl.setStyles({
					position:'absolute',
					top:y+10,
					opacity:0
				});
				ul.getElements('ul').setStyle('display','block');
				if(this.rtl){
					innerUl.setStyles({
						right:x,
						marginRight:-x
					});
				}else{
					innerUl.setStyles({
						left:x,
						marginLeft:-x
					});
				}
				//we call the createsubmenu function again, on the new UL
				this.createSubmenu(innerUl);
				//apply events to make the submenu appears when hovering the LI
				if(this.options.clickToOpen){
					li.addEvent('mouseenter',function(){
							$clear(li.retrieve('closeDelay'));
						}.bind(this)
					);
					li.getFirst('a').addEvent('click',function(e){
						e.stop();
						$clear(li.retrieve('closeDelay'));
						this.showChildList(li);
					}.bind(this));
				}else{
					li.addEvent('mouseenter',function(){
						$clear(li.retrieve('closeDelay'));
						li.store('openDelay',this.showChildList.delay(this.options.openDelay,this,li));
					}.bind(this));
				}
				li.addEvent('mouseleave', function(){
					$clear(li.retrieve('openDelay'));
					li.store('closeDelay',this.hideChildList.delay(this.options.closeDelay,this,li));
				}.bind(this));
			}
		},this);
	},
	
	//display submenu
	showChildList:function(li){
		var ul = li.getFirst('ul');
		var LIs =  $$(ul.getChildren('li'));
		var animation = li.retrieve('animation');
		//if the parent menu is not the main menu, the submenu must pop from the side
		if(li.getParent('ul')!=this.menu || this.options.mode == 'vertical'){
			animation.cancel();
			var anim ={
				0:{
					opacity:1
				},
				1:{
					opacity:1
				}
			};
			if(this.rtl){
				anim[0]['marginRight'] = 0;
			}else{
				anim[0]['marginLeft'] = 0;
			}
			animation.start(anim);
			var animobject={};
		//if the parent menu us the main menu, the submenu must drop down
		}else{
			var animobject = {0:{opacity:1}};
		}
		LIs.each(function(innerli,i){
			animobject[i+1]={
				top: 0,
				opacity:1
			};
		});
		li.setStyle('z-index',99);
		animation.start(animobject);
	},
	
	//hide the menu
	hideChildList:function(li){
		var animation = li.retrieve('animation');
		var ul = li.getFirst('ul');
		var LIs =  $$(ul.getChildren('li'));
		var offset = 0;
		var animobject={};
		LIs.each(function(innerli,i){
			animobject[i+1]={
				top:-offset,
				opacity:0
			};
			offset += innerli.getSize().y;
		});
		li.setStyle('z-index',1);
		//if the parent menu is not the main menu, the submenu must fold up, and go to the left
		if(li.getParent('ul')!=this.menu || this.options.mode == 'vertical'){
			animobject[1]=null;
			animation.cancel();
			animation.start(animobject);
			var anim = {
				0:{
					opacity:0
				},
				1:{
					opacity:0
				}
			};
			
			if(this.rtl){
				anim[0]['marginRight'] = -ul.getSize().x;
			}else{
				anim[0]['marginLeft'] = -ul.getSize().x;
			}
			animation.start(anim);
		//if the parent menu is the main menu, the submenu must just fold up
		}else{
			animobject[0]={opacity:0};
			animation.start(animobject);
		}
	}
});