/*
	DOMtab Version 3.1415927
	Updated March the First 2006
	written by Christian Heilmann
	check blog for updates: http://www.wait-till-i.com	
	free to use, not free to resell
*/

domtab={
	tabClass:'domtab', // class to trigger tabbing
	listClass:'domtabs', // class of the menus
	activeClass:'active', // class of current link
	contentElements:'div', // elements to loop through
	backToLinks:/#top/, // pattern to check "back to top" links
	printID:'domtabprintview', // id of the print all link
	showAllLinkText:'show all content', // text for the print all link
	prevNextIndicator:'doprevnext', // class to trigger prev and next links
	prevNextClass:'prevnext', // class of the prev and next list
	prevLabel:'previous', // HTML content of the prev link
	nextLabel:'next', // HTML content of the next link
	prevClass:'prev', // class for the prev link
	nextClass:'next', // class for the next link
	init:function(){
		var temp;
		if(!document.getElementById || !document.createTextNode){return;}
		var tempelm=document.getElementsByTagName('div');		
		for(var i=0;i<tempelm.length;i++){
			if(!domtab.cssjs('check',tempelm[i],domtab.tabClass)){continue;}
			domtab.initTabMenu(tempelm[i]);
			domtab.removeBackLinks(tempelm[i]);
			if(domtab.cssjs('check',tempelm[i],domtab.prevNextIndicator)){
				domtab.addPrevNext(tempelm[i]);
			}
			domtab.checkURL();
		}
		if(document.getElementById(domtab.printID) 
		   && !document.getElementById(domtab.printID).getElementsByTagName('a')[0]){
			var newlink=document.createElement('a');
			newlink.setAttribute('href','#');
			domtab.addEvent(newlink,'click',domtab.showAll,false);
			newlink.onclick=function(){return false;} // safari hack
			newlink.appendChild(document.createTextNode(domtab.showAllLinkText));
			document.getElementById(domtab.printID).appendChild(newlink);
		}
	},
	checkURL:function(){
		var id;
		var loc=window.location.toString();
		loc=/#/.test(loc)?loc.match(/#(\w.+)/)[1]:'';
		if(loc==''){return;}
		var elm=document.getElementById(loc);
		if(!elm){return;}
		var parentMenu=elm.parentNode.parentNode.parentNode;
		parentMenu.currentSection=loc;
		parentMenu.getElementsByTagName(domtab.contentElements)[0].style.display='none';
		domtab.cssjs('remove',parentMenu.getElementsByTagName('a')[0].parentNode,domtab.activeClass);
		var links=parentMenu.getElementsByTagName('a');
		for(i=0;i<links.length;i++){
			if(!links[i].getAttribute('href')){continue;}
			if(!/#/.test(links[i].getAttribute('href').toString())){continue;}
			id=links[i].href.match(/#(\w.+)/)[1];
			if(id==loc){
				var cur=links[i].parentNode.parentNode;
				domtab.cssjs('add',links[i].parentNode,domtab.activeClass);
				break;
			}
		}
		domtab.changeTab(elm,1);
		elm.focus();
		cur.currentLink=links[i];
		cur.currentSection=loc;
	},
	showAll:function(e){
		document.getElementById(domtab.printID).parentNode.removeChild(document.getElementById(domtab.printID));
		var tempelm=document.getElementsByTagName('div');		
		for(var i=0;i<tempelm.length;i++){
			if(!domtab.cssjs('check',tempelm[i],domtab.tabClass)){continue;}
			var sec=tempelm[i].getElementsByTagName(domtab.contentElements);
			for(var j=0;j<sec.length;j++){
				sec[j].style.display='block';
			}
		}
		var tempelm=document.getElementsByTagName('ul');		
		for(i=0;i<tempelm.length;i++){
			if(!domtab.cssjs('check',tempelm[i],domtab.prevNextClass)){continue;}
			tempelm[i].parentNode.removeChild(tempelm[i]);
			i--;
		}
		domtab.cancelClick(e);
	},
	addPrevNext:function(menu){
		var temp;
		var sections=menu.getElementsByTagName(domtab.contentElements);
		for(var i=0;i<sections.length;i++){
			temp=domtab.createPrevNext();
			if(i==0){
				temp.removeChild(temp.getElementsByTagName('li')[0]);
			}
			if(i==sections.length-1){
				temp.removeChild(temp.getElementsByTagName('li')[1]);
			}
			temp.i=i; // h4xx0r!
			temp.menu=menu;
			sections[i].appendChild(temp);
		}
	},
	removeBackLinks:function(menu){
		var links=menu.getElementsByTagName('a');
		for(var i=0;i<links.length;i++){
			if(!domtab.backToLinks.test(links[i].href)){continue;}
			links[i].parentNode.removeChild(links[i]);
			i--;
		}
	},
	initTabMenu:function(menu){
		var id;
		var lists=menu.getElementsByTagName('ul');
		for(var i=0;i<lists.length;i++){
			if(domtab.cssjs('check',lists[i],domtab.listClass)){
				var thismenu=lists[i];
				break;
			}
		}
		if(!thismenu){return;}
		thismenu.currentSection='';
		thismenu.currentLink='';
		var links=thismenu.getElementsByTagName('a');
		for(i=0;i<links.length;i++){
			if(!/#/.test(links[i].getAttribute('href').toString())){continue;}
			id=links[i].href.match(/#(\w.+)/)[1];
			if(document.getElementById(id)){
				domtab.addEvent(links[i],'click',domtab.showTab,false);
				links[i].onclick=function(){return false;} // safari hack
				domtab.changeTab(document.getElementById(id),0);
			}
		}
		id=links[0].href.match(/#(\w.+)/)[1];
		if(document.getElementById(id)){
			domtab.changeTab(document.getElementById(id),1);
			thismenu.currentSection=id;
			thismenu.currentLink=links[0];
			domtab.cssjs('add',links[0].parentNode,domtab.activeClass);
		}
	},
	createPrevNext:function(){
		// this would be so much easier with innerHTML, darn you standards fetish!
		var temp=document.createElement('ul');
		temp.className=domtab.prevNextClass;
		temp.appendChild(document.createElement('li'));
		temp.getElementsByTagName('li')[0].appendChild(document.createElement('a'));
		temp.getElementsByTagName('a')[0].setAttribute('href','#');
		temp.getElementsByTagName('a')[0].innerHTML=domtab.prevLabel;
		temp.getElementsByTagName('li')[0].className=domtab.prevClass;
		temp.appendChild(document.createElement('li'));
		temp.getElementsByTagName('li')[1].appendChild(document.createElement('a'));
		temp.getElementsByTagName('a')[1].setAttribute('href','#');
		temp.getElementsByTagName('a')[1].innerHTML=domtab.nextLabel;
		temp.getElementsByTagName('li')[1].className=domtab.nextClass;
		domtab.addEvent(temp.getElementsByTagName('a')[0],'click',domtab.navTabs,false);
		domtab.addEvent(temp.getElementsByTagName('a')[1],'click',domtab.navTabs,false);
		// safari fix
		temp.getElementsByTagName('a')[0].onclick=function(){return false;}
		temp.getElementsByTagName('a')[1].onclick=function(){return false;}
		return temp;
	},
	navTabs:function(e){
		var li=domtab.getTarget(e);
		var menu=li.parentNode.parentNode.menu;
		var count=li.parentNode.parentNode.i;
		var section=menu.getElementsByTagName(domtab.contentElements);
		var links=menu.getElementsByTagName('a');
		var othercount=(li.parentNode.className==domtab.prevClass)?count-1:count+1;
		section[count].style.display='none';
		domtab.cssjs('remove',links[count].parentNode,domtab.activeClass);
		section[othercount].style.display='block';
		domtab.cssjs('add',links[othercount].parentNode,domtab.activeClass);
		var parent=links[count].parentNode.parentNode;
		parent.currentLink=links[othercount];
		parent.currentSection=links[othercount].href.match(/#(\w.+)/)[1];
		domtab.cancelClick(e);
	},
	changeTab:function(elm,state){
		do{
			elm=elm.parentNode;
		} while(elm.nodeName.toLowerCase()!=domtab.contentElements)
		elm.style.display=state==0?'none':'block';
	},
	showTab:function(e){
		var o=domtab.getTarget(e);
		if(o.parentNode.parentNode.currentSection!=''){
			domtab.changeTab(document.getElementById(o.parentNode.parentNode.currentSection),0);
			domtab.cssjs('remove',o.parentNode.parentNode.currentLink.parentNode,domtab.activeClass);
		}
		var id=o.href.match(/#(\w.+)/)[1];
		o.parentNode.parentNode.currentSection=id;
		o.parentNode.parentNode.currentLink=o;
		domtab.cssjs('add',o.parentNode,domtab.activeClass);
		domtab.changeTab(document.getElementById(id),1);
		document.getElementById(id).focus();
		domtab.cancelClick(e);
	},
/* helper methods */
	getTarget:function(e){
		var target = window.event ? window.event.srcElement : e ? e.target : null;
		if (!target){return false;}
		if (target.nodeName.toLowerCase() != 'a'){target = target.parentNode;}
		return target;
	},
	cancelClick:function(e){
		if (window.event){
			window.event.cancelBubble = true;
			window.event.returnValue = false;
			return;
		}
		if (e){
			e.stopPropagation();
			e.preventDefault();
		}
	},
	addEvent: function(elm, evType, fn, useCapture){
		if (elm.addEventListener) 
		{
			elm.addEventListener(evType, fn, useCapture);
			return true;
		} else if (elm.attachEvent) {
			var r = elm.attachEvent('on' + evType, fn);
			return r;
		} else {
			elm['on' + evType] = fn;
		}
	},
	cssjs:function(a,o,c1,c2){
		switch (a){
			case 'swap':
				o.className=!domtab.cssjs('check',o,c1)?o.className.replace(c2,c1):o.className.replace(c1,c2);
			break;
			case 'add':
				if(!domtab.cssjs('check',o,c1)){o.className+=o.className?' '+c1:c1;}
			break;
			case 'remove':
				var rep=o.className.match(' '+c1)?' '+c1:c1;
				o.className=o.className.replace(rep,'');
			break;
			case 'check':
				var found=false;
				var temparray=o.className.split(' ');
				for(var i=0;i<temparray.length;i++){
					if(temparray[i]==c1){found=true;}
				}
				return found;
			break;
		}
	}
}
domtab.addEvent(window, 'load', domtab.init, false);
	
