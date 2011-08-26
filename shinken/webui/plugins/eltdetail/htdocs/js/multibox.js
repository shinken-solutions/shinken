/**************************************************************

	Script		: MultiBox
	Version		: 1.4.1
	Authors		: Samuel Birch
	Desc		: Supports jpg, gif, png, flash, flv, mov, wmv, mp3, html, iframe
	Licence		: Open Source MIT Licence


**************************************************************/

var MultiBox = new Class({
	
	getOptions: function(){
		return {
			initialWidth: 250,
			initialHeight: 250,
			container: document.body, //this will need to be setup to the box open in relation to this.
			overlay: false, //this will be a reference to an overlay instance. - TODO: implement below.
			contentColor: '#FFF',
			showNumbers: true,
			showControls: true,
			//showThumbnails: false,
			//autoPlay: false,
			//waitDuration: 2000,
			descClassName: false,
			descMinWidth: 400,
			descMaxWidth: 600,
			movieWidth: 400,
			movieHeight: 300,
			offset: {x:0, y:0},
			fixedTop: false,
			path: 'files/',
			_onOpen: $empty,
			_onClose: $empty,
			openFromLink: true
			//relativeToWindow: true
		};
	},

	initialize: function(className, options){
		this.setOptions(this.getOptions(), options);
		
		this.openClosePos = {};
		this.timer = 0;
		this.contentToLoad = {};
		this.index = 0;
		this.opened = false;
		this.contentObj = {};
		this.containerDefaults = {};
		this.createArray = [];
		
		if(this.options.useOverlay){
			this.overlay = new Overlay({container: this.options.container, onClick:this.close.bind(this)});
		}
		this.overlay = this.options.overlay;
		if(this.overlay){
			this.overlay.setOnClick(this.close.bind(this));
		}
		
		this.content = $$('.'+className);
		if(this.options.descClassName){
			this.descriptions = $$('.'+this.options.descClassName);
			this.descriptions.each(function(el){
				el.setStyle('display', 'none');
			});
		}
		
		this.container = new Element('div').addClass('MultiBoxContainer').injectInside(this.options.container);
		this.iframe = new Element('iframe').setProperties({
			'id': 'multiBoxIframe',
			'name': 'mulitBoxIframe',
			'src': 'javascript:void(0);',
			'frameborder': 0,
			'scrolling': 'no'
		}).setStyles({
			'position': 'absolute',
			'top': -20,
			'left': -20,
			'filter': 'progid:DXImageTransform.Microsoft.Alpha(style=0,opacity=0)',
			'opacity': 0
		}).inject(this.container);
		this.box = new Element('div').addClass('MultiBoxContent').inject(this.container);
		
		this.closeButton = new Element('div').addClass('MultiBoxClose').inject(this.container).addEvent('click', this.close.bind(this));
		
		this.controlsContainer = new Element('div').addClass('MultiBoxControlsContainer').inject(this.container);
		this.controls = new Element('div').addClass('MultiBoxControls').inject(this.controlsContainer);
		
		this.previousButton = new Element('div').addClass('MultiBoxPrevious').inject(this.controls).addEvent('click', this.previous.bind(this));
		this.nextButton = new Element('div').addClass('MultiBoxNext').inject(this.controls).addEvent('click', this.next.bind(this));
		
		this.title = new Element('div').addClass('MultiBoxTitle').inject(this.controls);
		this.titleMargin = this.title.getStyle('margin-left');
		this.number = new Element('div').addClass('MultiBoxNumber').inject(this.controls);
		this.description = new Element('div').addClass('MultiBoxDescription').inject(this.controls);
		
		
		
		if(this.content.length == 1){
			this.title.setStyles({
				'margin-left': 0
			});
			this.description.setStyles({
				'margin-left': 0
			});
			this.previousButton.setStyle('display', 'none');
			this.nextButton.setStyle('display', 'none');
			this.number.setStyle('display', 'none');
		}
		
		new Element('div').setStyle('clear', 'both').inject(this.controls);
		
		this.content.each(function(el,i){
			el.index = i;
			el.addEvent('click', function(e){
				new Event(e).stop();
				this.open(el);
			}.bind(this));
			if(el.href.indexOf('#') > -1){
				el.content = $(el.href.substr(el.href.indexOf('#')+1));
				if(el.content){el.content.setStyle('display','none');}
			}
		}, this);
		
		this.containerEffects = new Fx.Morph(this.container, {duration: 400, transition: Fx.Transitions.Sine.easeInOut});
		this.iframeEffects = new Fx.Morph(this.iframe, {duration: 400, transition: Fx.Transitions.Sine.easeInOut});
		this.controlEffects = new Fx.Morph(this.controlsContainer, {duration: 300, transition: Fx.Transitions.Sine.easeInOut});
		
		this.reset();
	},
	
	setContentType: function(link){
		var str = link.href.substr(link.href.lastIndexOf('.')+1).toLowerCase();
		var contentOptions = {};
		if($chk(link.rel)){
			var optArr = link.rel.split(',');
			optArr.each(function(el){
				var ta = el.split(':');
				contentOptions[ta[0]] = ta[1];
			});
		}
		
		if(contentOptions.type != undefined){
			str = contentOptions.type;
		}
		
		this.contentObj = {};
		this.contentObj.url = link.href;
		this.contentObj.src = link.href;
		this.contentObj.xH = 0;
		
		if(contentOptions.width){
			this.contentObj.width = contentOptions.width;
		}else{
			this.contentObj.width = this.options.movieWidth;
		}
		if(contentOptions.height){
			this.contentObj.height = contentOptions.height;	
		}else{
			this.contentObj.height = this.options.movieHeight;
		}
		if(contentOptions.panel){
			this.panelPosition = contentOptions.panel;
		}else{
			this.panelPosition = this.options.panel;
		}
		
		switch(str){
			case 'jpg':
			case 'image':
			case 'gif':
			case 'png':
				this.type = 'image';
				break;
			case 'swf':
				this.type = 'flash';
				break;
			case 'youtube':
				this.type = 'youtube';
				break;
			case 'flv':
				this.type = 'flashVideo';
				this.contentObj.xH = 70;
				break;
			case 'mov':
				this.type = 'quicktime';
				break;
			case 'wmv':
				this.type = 'windowsMedia';
				break;
			case 'rv':
			case 'rm':
			case 'rmvb':
				this.type = 'real';
				break;
			case 'mp3':
				this.type = 'flashMp3';
				this.contentObj.width = 320;
				this.contentObj.height = 70;
				break;
			case 'element':
				this.type = 'htmlelement';
				this.elementContent = link.content;
				this.elementContent.setStyles({
					display: 'block',
					opacity: 0
				})
	
				if(contentOptions.width){
					this.contentObj.width = contentOptions.width;
					
				}else if(this.elementContent.getStyle('width') != 'auto'){
					this.contentObj.width = this.elementContent.getStyle('width');
				}
				
				if(contentOptions.height){
					this.contentObj.height = contentOptions.height;	
				}else{
					this.contentObj.height = this.elementContent.getSize().y;
				}
				this.elementContent.setStyles({
					display: 'none',
					opacity: 1
				})
				break;
				
			default:
				
				this.type = 'iframe';
				if(contentOptions.ajax){
					this.type = 'ajax';
				}
				break;
		}
	},
	
	reset: function(){
		this.container.setStyles({
			'opacity': 0,
			'display': 'none'
		});
		this.controlsContainer.setStyles({
			'height': 0
		});
		this.removeContent();
		this.previousButton.removeClass('MultiBoxButtonDisabled');
		this.nextButton.removeClass('MultiBoxButtonDisabled');
		this.opened = false;
	},
	
	getOpenClosePos: function(el){
		if (this.options.openFromLink) {
			if (el.getFirst()) {
				var w = el.getFirst().getCoordinates().width - (this.container.getStyle('border').toInt() * 2);
				if (w < 0) {
					w = 0
				}
				var h = el.getFirst().getCoordinates().height - (this.container.getStyle('border').toInt() * 2);
				if (h < 0) {
					h = 0
				}
				this.openClosePos = {
					width: w,
					height: h,
					top: el.getFirst().getCoordinates().top,
					left: el.getFirst().getCoordinates().left
				};
			}
			else {
				var w = el.getCoordinates().width - (this.container.getStyle('border').toInt() * 2);
				if (w < 0) {
					w = 0
				}
				var h = el.getCoordinates().height - (this.container.getStyle('border').toInt() * 2);
				if (h < 0) {
					h = 0
				}
				this.openClosePos = {
					width: w,
					height: h,
					top: el.getCoordinates().top,
					left: el.getCoordinates().left
				};
			}
		}else{
			var border = this.container.getStyle('border').toInt();
			
			if(this.options.fixedTop){
				var top = this.options.fixedTop;
			}else{
				var top = ((window.getHeight()/2)-(this.options.initialHeight/2) - border)+this.options.offset.y + window.getScroll().y;
			}
			this.openClosePos = {
				width: this.options.initialWidth,
				height: this.options.initialHeight,
				top: top,
				left: ((window.getWidth()/2)-(this.options.initialWidth/2)-border)+this.options.offset.x
			};
		}
		return this.openClosePos;
	},
	
	open: function(el){
		this.options._onOpen();
	
		this.index = this.content.indexOf(el);
		
		this.openId = el.getProperty('id');
		
		var border = this.container.getStyle('border').toInt();
		
		if(!this.opened){
			this.opened = true;
			
			if(this.options.overlay){
				this.overlay.show();
			}

			this.container.setStyles(this.getOpenClosePos(el));
			this.container.setStyles({
				opacity: 0,
				display: 'block'
			});
			
			if(this.options.fixedTop){
				var top = this.options.fixedTop;
			}else{
				var top = ((window.getHeight()/2)-(this.options.initialHeight/2) - border)+this.options.offset.y+window.getScroll().y;
			}
			
			
			this.containerEffects.start({
				width: this.options.initialWidth,
				height: this.options.initialHeight,
				top: top,
				left: ((window.getWidth()/2)-(this.options.initialWidth/2)-border)+this.options.offset.x,
				opacity: [0, 1]
			});
			
			this.load(this.index);
		
		}else{
			if (this.options.showControls) {
				this.hideControls();
			}
			this.getOpenClosePos(this.content[this.index]);
			this.timer = this.hideContent.bind(this).delay(500);
			this.timer = this.load.pass(this.index, this).delay(1100);
			
		}
		
	},
	
	create: function(obj){
		/*
		obj = {
			url: 'myurl',  *
			title: 'my title',
			description: 'my description',
			type: 'image',
			width: 400,
			height: 300
		}
		*/
		if(this.createArray.contains(obj.url)){
			var index = this.createArray.indexOf(obj.url);
			var a = this.content[index];
		}else{
			
			var id = 'mbDirect_' + $time();
			var rel = [];
			if(obj.type){rel.push('type:'+obj.type)}
			if(obj.width){rel.push('width:'+obj.width)}
			if(obj.height){rel.push('height:'+obj.height)}
			
			var a = new Element('a', {
				'href': obj.url,
				'id': id,
				'title': obj.title || '',
				'rel': rel.join(',')
			});
			var desc = new Element('div', {
				'class': id,
				'html': obj.description || ''
			})
		
			this.createArray.push(obj.url);
			this.content.push(a);
			var index = this.content.length-1;
			
			if(this.options.descClassName){
				this.descriptions.include(desc);
			}
		}
		this.open(a);
	},
	
	getContent: function(index){
		this.setContentType(this.content[index]);
		var desc = false;
		if(this.options.descClassName){
		this.descriptions.each(function(el,i){
			if(el.hasClass(this.openId)){
				desc = el.clone();
			}
		},this);
		}
		this.contentToLoad = {
			title: this.content[index].title || '&nbsp;',
			desc: desc,
			number: index+1
		};
	},
	
	close: function(){
		if(this.options.overlay){
			this.overlay.hide();
		}
		if (this.options.showControls) {
			this.hideControls();
		}
		this.hideContent();
		this.containerEffects.cancel();
		this.zoomOut.bind(this).delay(500);
		this.options._onClose();
	},
	
	zoomOut: function(){
		this.iframeEffects.start({
			width: this.openClosePos.width,
			height: this.openClosePos.height
		});
		this.containerEffects.start({
			width: this.openClosePos.width,
			height: this.openClosePos.height,
			top: this.openClosePos.top,
			left: this.openClosePos.left,
			opacity: 0
		});
		this.reset.bind(this).delay(500);
	},
	
	load: function(index){
		this.box.addClass('MultiBoxLoading');
		this.getContent(index);
		if(this.type == 'image'){
			var xH = this.contentObj.xH;
			this.contentObj = new Asset.image(this.content[index].href, {onload: this.resize.bind(this)});
			this.contentObj.xH = xH;
		}else{
			this.resize();
		}
	},
	
	resize: function(){
		if(this.tempSRC != this.contentObj.src){
			
			var border = this.container.getStyle('border').toInt();
			
			if (this.options.fixedTop) {
				var top = this.options.fixedTop;
			}
			else {
				var top = ((window.getHeight() / 2) - ((Number(this.contentObj.height) + this.contentObj.xH) / 2) - border + window.getScrollTop()) + this.options.offset.y;
			}
			var left = ((window.getWidth() / 2) - (this.contentObj.width.toInt() / 2) - border) + this.options.offset.x;
			if (top < 0) {
				top = 0
			}
			if (left < 0) {
				left = 0
			}
			
			this.containerEffects.cancel();
			this.containerEffects.start({
				width: this.contentObj.width,
				height: Number(this.contentObj.height) + this.contentObj.xH,
				top: top,
				left: left,
				opacity: 1
			});
			this.iframeEffects.start({
				width: Number(this.contentObj.width) + (border*2),
				height: Number(this.contentObj.height) + this.contentObj.xH + (border*2)
			});
			this.timer = this.showContent.bind(this).delay(500);
			this.tempSRC = this.contentObj.src;
		}
	},
	
	showContent: function(){
		this.tempSRC = '';
		this.box.removeClass('MultiBoxLoading');
		this.removeContent();
		
		this.contentContainer = new Element('div').setProperties({id: 'MultiBoxContentContainer'}).setStyles({opacity: 0, width: this.contentObj.width+'px', height: (Number(this.contentObj.height)+this.contentObj.xH)+'px'}).injectInside(this.box);
		
		if(this.type == 'image'){
			this.contentObj.injectInside(this.contentContainer);
			
		}else if(this.type == 'iframe'){
			new Element('iframe').setProperties({
				id: 'iFrame'+new Date().getTime(), 
				width: this.contentObj.width,
				height: this.contentObj.height,
				src: this.contentObj.url,
				frameborder: 0,
				scrolling: 'auto'
			}).injectInside(this.contentContainer);
			
		}else if(this.type == 'htmlelement'){
			this.contentContainer.setStyle('overflow', 'auto');
			this.elementContentParent = this.elementContent.getParent();
			this.elementContent.setStyle('display','block').injectInside(this.contentContainer);
			
		}else if(this.type == 'ajax'){
			new Request.HTML({
				update: $('MultiBoxContentContainer'),
				autoCancel: true
			}).get(this.contentObj.url);
			
		}else{
			var obj = this.createEmbedObject().injectInside(this.contentContainer);
			if(this.str != ''){
				$('MultiBoxMediaObject').innerHTML = this.str;
			}
		}
		
		this.contentEffects = new Fx.Morph(this.contentContainer, {duration: 500, transition: Fx.Transitions.linear});
		this.contentEffects.start({
			opacity: 1
		});
		
		this.title.set('html', this.contentToLoad.title);
		if(this.content.length > 1){
			this.number.set('html', this.contentToLoad.number+' of '+this.content.length);
		}else{
			this.number.set('html','');
		}
		if (this.options.descClassName) {
			if (this.description.getFirst()) {
				this.description.getFirst().destroy();
			}
			if(this.contentToLoad.desc){
				this.contentToLoad.desc.inject(this.description).setStyles({
					display: 'block'
				});
			}
		}
		//this.removeContent.bind(this).delay(500);
		if (this.options.showControls) {
			if(this.contentToLoad.title != '&nbsp;' || this.content.length > 1){
				this.timer = this.showControls.bind(this).delay(800);
			}
		}
	},
	
	hideContent: function(){
		this.box.addClass('MultiBoxLoading');
		this.contentEffects.start({
			opacity: 0
		});
		this.removeContent.bind(this).delay(500);
	},
	
	removeContent: function(){
		if($('MultiBoxMediaObject')){
			$('MultiBoxMediaObject').empty();
			$('MultiBoxMediaObject').destroy();
		}
		if($('MultiBoxContentContainer')){
			if(this.type == 'htmlelement'){
				this.elementContent.setStyle('display','none').inject(this.elementContentParent);
			}
			$('MultiBoxContentContainer').destroy();	
		}
	},
	
	showControls: function(){
		this.clicked = false;
		
		if(this.container.getStyle('height') != 'auto'){
			this.containerDefaults.height = this.container.getStyle('height')
			this.containerDefaults.backgroundColor = this.options.contentColor;
		}
		
		this.container.setStyles({
			//'backgroundColor': this.controls.getStyle('backgroundColor'),
			'height': 'auto'
		});
		
		if(this.content.length > 1){
			this.previousButton.setStyle('visibility', 'visible');
			this.nextButton.setStyle('visibility', 'visible');
			this.title.setStyle('margin-left', this.titleMargin);
			
			if(this.contentToLoad.number == 1){
				this.previousButton.addClass('MultiBoxPreviousDisabled');
			}else{
				this.previousButton.removeClass('MultiBoxPreviousDisabled');
			}
			if(this.contentToLoad.number == this.content.length){
				this.nextButton.addClass('MultiBoxNextDisabled');
			}else{
				this.nextButton.removeClass('MultiBoxNextDisabled');
			}
		}else{
			this.previousButton.setStyle('visibility', 'hidden');
			this.nextButton.setStyle('visibility', 'hidden');
			this.title.setStyle('margin-left', 0);
		}
		
		this.controlEffects.start({'height': this.controls.getCoordinates().height});
		this.iframeEffects.start({'height': this.iframe.getStyle('height').toInt()+this.controls.getStyle('height').toInt()});
		
		if(this.options.overlay){
			this.options.overlay.position();
		}

	},
	
	hideControls: function(num){
		this.iframeEffects.start({'height': this.iframe.getStyle('height').toInt()-this.controls.getStyle('height').toInt()});
		this.controlEffects.start({'height': 0}).chain(function(){
			this.container.setStyles(this.containerDefaults);
		}.bind(this));
	},
	
	showThumbnails: function(){
		
	},
	
	next: function(){
		if(this.index < this.content.length-1){
			this.index++;
			this.openId = this.content[this.index].getProperty('id');
			if (this.options.showControls) {
				this.hideControls();
			}
			this.getOpenClosePos(this.content[this.index]);
			//this.getContent(this.index);
			this.timer = this.hideContent.bind(this).delay(500);
			this.timer = this.load.pass(this.index, this).delay(1100);
		}
	},
	
	previous: function(){
		if(this.index > 0){
			this.index--;
			this.openId = this.content[this.index].getProperty('id');
			if (this.options.showControls) {
				this.hideControls();
			}
			this.getOpenClosePos(this.content[this.index]);
			//this.getContent(this.index);
			this.timer = this.hideContent.bind(this).delay(500);
			this.timer = this.load.pass(this.index, this).delay(1000);
		}
	},
	
	createEmbedObject: function(){
		if(this.type == 'flash'){
			var url = this.contentObj.url;
			
			var obj = new Element('div').setProperties({id: 'MultiBoxMediaObject'});
			this.str = '<object classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000" codebase="http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=9,0,28,0" '
			this.str += 'width="'+this.contentObj.width+'" ';
			this.str += 'height="'+this.contentObj.height+'" ';
			this.str += 'title="MultiBoxMedia">';
  			this.str += '<param name="movie" value="'+url+'" />'
  			this.str += '<param name="quality" value="high" />';
  			this.str += '<embed src="'+url+'" ';
  			this.str += 'quality="high" pluginspage="http://www.adobe.com/shockwave/download/download.cgi?P1_Prod_Version=ShockwaveFlash" type="application/x-shockwave-flash" ';
  			this.str += 'width="'+this.contentObj.width+'" ';
  			this.str += 'height="'+this.contentObj.height+'"></embed>';
			this.str += '</object>';
			
		}
		
		if(this.type == 'youtube'){
			var url = this.contentObj.url;
			
			var s = url.indexOf('v=')+2;
			var e = url.indexOf('&', s);
			url = url.substring(s,e);
			url = 'http://www.youtube.com/v/'+url+'&h1=en&fs=1';
			//console.log(url)
			
			var obj = new Element('div').setProperties({id: 'MultiBoxMediaObject'});
			this.str = '<object classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000" codebase="http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=9,0,28,0" '
			this.str += 'width="'+this.contentObj.width+'" ';
			this.str += 'height="'+this.contentObj.height+'" ';
			this.str += 'title="MultiBoxMedia">';
  			this.str += '<param name="movie" value="'+url+'" />'
  			this.str += '<param name="quality" value="high" />';
  			this.str += '<param name="allowFullScreen" value="true"></param>';
  			this.str += '<embed src="'+url+'" ';
  			this.str += 'quality="high" pluginspage="http://www.adobe.com/shockwave/download/download.cgi?P1_Prod_Version=ShockwaveFlash" type="application/x-shockwave-flash" ';
  			this.str += 'allowfullscreen="true" ';
  			this.str += 'width="'+this.contentObj.width+'" ';
  			this.str += 'height="'+this.contentObj.height+'"></embed>';
			this.str += '</object>';
			
		}
		
		if(this.type == 'flashVideo'){
			//var url = this.contentObj.url.substring(0, this.contentObj.url.lastIndexOf('.'));
			var url = this.contentObj.url;
			
			var obj = new Element('div').setProperties({id: 'MultiBoxMediaObject'});
			this.str = '<object classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000" codebase="http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=9,0,28,0" '
			this.str += 'width="'+this.contentObj.width+'" ';
			this.str += 'height="'+(Number(this.contentObj.height)+this.contentObj.xH)+'" ';
			this.str += 'title="MultiBoxMedia">';
  			this.str += '<param name="movie" value="'+this.options.path+'flvplayer.swf" />'
  			this.str += '<param name="quality" value="high" />';
  			this.str += '<param name="salign" value="TL" />';
  			this.str += '<param name="scale" value="noScale" />';
  			this.str += '<param name="FlashVars" value="path='+url+'" />';
  			this.str += '<embed src="'+this.options.path+'flvplayer.swf" ';
  			this.str += 'quality="high" pluginspage="http://www.adobe.com/shockwave/download/download.cgi?P1_Prod_Version=ShockwaveFlash" type="application/x-shockwave-flash" ';
  			this.str += 'width="'+this.contentObj.width+'" ';
  			this.str += 'height="'+(Number(this.contentObj.height)+this.contentObj.xH)+'"';
  			this.str += 'salign="TL" ';
  			this.str += 'scale="noScale" ';
  			this.str += 'FlashVars="path='+url+'"';
  			this.str += '></embed>';
			this.str += '</object>';
			
		}
		
		if(this.type == 'flashMp3'){
			var url = this.contentObj.url;
			
			var obj = new Element('div').setProperties({id: 'MultiBoxMediaObject'});
			this.str = '<object classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000" codebase="http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=9,0,28,0" '
			this.str += 'width="'+this.contentObj.width+'" ';
			this.str += 'height="'+this.contentObj.height+'" ';
			this.str += 'title="MultiBoxMedia">';
  			this.str += '<param name="movie" value="'+this.options.path+'mp3player.swf" />'
  			this.str += '<param name="quality" value="high" />';
  			this.str += '<param name="salign" value="TL" />';
  			this.str += '<param name="scale" value="noScale" />';
  			this.str += '<param name="FlashVars" value="path='+url+'" />';
  			this.str += '<embed src="'+this.options.path+'mp3player.swf" ';
  			this.str += 'quality="high" pluginspage="http://www.adobe.com/shockwave/download/download.cgi?P1_Prod_Version=ShockwaveFlash" type="application/x-shockwave-flash" ';
  			this.str += 'width="'+this.contentObj.width+'" ';
  			this.str += 'height="'+this.contentObj.height+'"';
  			this.str += 'salign="TL" ';
  			this.str += 'scale="noScale" ';
  			this.str += 'FlashVars="path='+url+'"';
  			this.str += '></embed>';
			this.str += '</object>';
		}
		
		if(this.type == 'quicktime'){
			var obj = new Element('div').setProperties({id: 'MultiBoxMediaObject'});
			this.str = '<object  type="video/quicktime" classid="clsid:02BF25D5-8C17-4B23-BC80-D3488ABDDC6B" codebase="http://www.apple.com/qtactivex/qtplugin.cab"';
			this.str += ' width="'+this.contentObj.width+'" height="'+this.contentObj.height+'">';
			this.str += '<param name="src" value="'+this.contentObj.url+'" />';
			this.str += '<param name="autoplay" value="true" />';
			this.str += '<param name="controller" value="true" />';
			this.str += '<param name="enablejavascript" value="true" />';
			this.str += '<embed src="'+this.contentObj.url+'" autoplay="true" pluginspage="http://www.apple.com/quicktime/download/" width="'+this.contentObj.width+'" height="'+this.contentObj.height+'"></embed>';
			this.str += '<object/>';
			
		}
		
		if(this.type == 'windowsMedia'){
			var obj = new Element('div').setProperties({id: 'MultiBoxMediaObject'});
			this.str = '<object  type="application/x-oleobject" classid="CLSID:22D6f312-B0F6-11D0-94AB-0080C74C7E95" codebase="http://activex.microsoft.com/activex/controls/mplayer/en/nsmp2inf.cab#Version=6,4,7,1112"';
			this.str += ' width="'+this.contentObj.width+'" height="'+this.contentObj.height+'">';
			this.str += '<param name="filename" value="'+this.contentObj.url+'" />';
			this.str += '<param name="Showcontrols" value="true" />';
			this.str += '<param name="autoStart" value="true" />';
			this.str += '<embed type="application/x-mplayer2" src="'+this.contentObj.url+'" Showcontrols="true" autoStart="true" width="'+this.contentObj.width+'" height="'+this.contentObj.height+'"></embed>';
			this.str += '<object/>';
			
		}
		
		if(this.type == 'real'){
			var obj = new Element('div').setProperties({id: 'MultiBoxMediaObject'});
			this.str = '<object classid="clsid:CFCDAA03-8BE4-11cf-B84B-0020AFBBCCFA"';
			this.str += ' width="'+this.contentObj.width+'" height="'+this.contentObj.height+'">';
			this.str += '<param name="src" value="'+this.contentObj.url+'" />';
			this.str += '<param name="controls" value="ImageWindow" />';
			this.str += '<param name="autostart" value="true" />';
			this.str += '<embed src="'+this.contentObj.url+'" controls="ImageWindow" autostart="true" width="'+this.contentObj.width+'" height="'+this.contentObj.height+'"></embed>';
			this.str += '<object/>';
			
		}
		
		return obj;
	}
	
});
MultiBox.implement(new Options);
MultiBox.implement(new Events);