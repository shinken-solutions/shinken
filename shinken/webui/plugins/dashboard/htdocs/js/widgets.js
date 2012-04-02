/*Copyright (C) 2009-2012 :
     Gabes Jean, naparuba@gmail.com
     Gerhard Lausser, Gerhard.Lausser@consol.de
     Gregory Starck, g.starck@gmail.com
     Hartmut Goebel, h.goebel@goebel-consult.de
 
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



var save_state = false;




// Now try to load widgets in a dynamic way
function AddWidget(url, placeId){
    $.get(url, function(html){
	$.fn.AddEasyWidget(html, placeId, {});
    });
}

  // when we add a new widget, we also save the current widgets
// configuration for this user
function AddNewWidget(url, placeId){
    AddWidget(url, placeId);
    console.log('Add new widget');
    save_state = true;
}



$(function(){

  // where we stock all current widgets loaded, and their options
  widgets = [];

  // Very basic usage  
  $.fn.EasyWidgets(
	{
    effects : {
      effectDuration : 100,
      widgetShow : 'slide',
      widgetHide : 'slide',
      widgetClose : 'slide',
      widgetExtend : 'slide',
      widgetCollapse : 'slide',
      widgetOpenEdit : 'slide',
      widgetCloseEdit : 'slide',
      widgetCancelEdit : 'slide'
    },

   callbacks : {
      onCollapse : function(link, widget){
          var name = widget.attr('id');
          var key = name+'_collapsed';
          $.post("/user/save_pref", { 'key' : key, 'value' : true});
      },
      onExtend : function(link, widget){
        alert('onentend callback :: Link: ' + link + ' - Widget: ' + widget.attr('id'));
      },
      onClose : function(link, widget){
	   // On close, save all
	   save_state = true;
       }
       
   }
  });
  


function find_widget(name){
    res = -1;
    w = $.each(widgets, function(idx, w){
	if(name == w.id){
	    res = w;
	}
    });
    
    return res;
}


// We will look if we need to save the current state and options or not
function save_new_widgets(){
     if(!save_state){return;}
     // No more need
     save_state = false;

     var widgets_ids = [];
     var save_widgets_list = false;
    $('.widget').each(function(idx, w){
	
	// If the widget is closed, don't save it
	if($(this).css('display') == 'none'){return;}

	id = w.id;
	var widget = find_widget(id);
	//alert('Find widget'+widget);
	// Find the widget and check if it was not closed
	if(widget != -1){
	    
	    //alert('Loop over a widget'+w.id+''+w.position+''+w.base_url);
            var o = {'id' : widget.id, 'position' : widget.position, 'base_url' : widget.base_url, 'options' : widget.options};
            widgets_ids.push(o);
	}
         /*if(!w.hasOwnProperty('is_saved')){
           save_widgets_list = true;
           //alert('Saving widget'+w.id);
           var key= 'widget_'+w.id;
           var value = JSON.stringify(w);
           //alert('with key:value'+key+' '+value);
           $.post("/user/save_pref", { 'key' : key, 'value' : value});
           w.is_saved=true;
         }*/
     });

    console.log('Need to save widgets list'+JSON.stringify(widgets_ids));
    $.post("/user/save_pref", { 'key' : 'widgets', 'value' : JSON.stringify(widgets_ids)});
  }




setInterval( save_new_widgets, 1000);


});
