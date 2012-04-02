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
      }

   }
  });
  
});





// We will look if we need to save the current state and options or not
function save_new_widgets(){
     if(!save_state){return;}
     // No more need
     save_state = false;
     
     var widgets_ids = [];
     var save_widgets_list = false;
     $.each(widgets, function(idx, w){
         var o = {'id' : w.id, 'position' : w.position, 'base_url' : w.base_url, 'options' : w.options};
         widgets_ids.push(o);
         if(!w.hasOwnProperty('is_saved')){
           save_widgets_list = true;
           //alert('Saving widget'+w.id);
           var key= 'widget_'+w.id;
           var value = JSON.stringify(w);
           //alert('with key:value'+key+' '+value);
           $.post("/user/save_pref", { 'key' : key, 'value' : value});
           w.is_saved=true;
         }
     });

     // Look if weneed to save the widget lists
     if(save_widgets_list){
         alert('Need to save widgets list'+JSON.stringify(widgets_ids));
         $.post("/user/save_pref", { 'key' : 'widgets', 'value' : JSON.stringify(widgets_ids)});
     }

  }



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
    save_state = true;
}

setInterval( save_new_widgets, 1000);