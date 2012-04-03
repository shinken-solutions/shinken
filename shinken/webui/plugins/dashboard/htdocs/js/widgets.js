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


function ask_for_widgets_state_save(){
    save_state = true;
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
    console.log('Add new widget');
    ask_for_widgets_state_save();
    //save_state = true;
}


function find_widget(name){
    res = -1;
    w = $.each(widgets, function(idx, w){
	if(name == w.id){
	    res = w;
	}
    });
    
    return res;
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
		    var w = find_widget(widget.attr('id'));
                    if(w != -1){
                        // We finally save the new position
                        w.collapsed = true;
                    }
		    ask_for_widgets_state_save();
		    //save_state = true;
		},
		onExtend : function(link, widget){
		    console.log('onentend callback :: Link: ' + link + ' - Widget: ' + widget.attr('id'));
		    var w = find_widget(widget.attr('id'));
                    if(w != -1){
                        // We finally save the new position
                        w.collapsed = false;
                    }
		    ask_for_widgets_state_save();
                    //save_state = true;
		},
		onClose : function(link, widget){
		    // On close, save all
		    ask_for_widgets_state_save();
		    //save_state = true;
		},
		onChangePositions : function(positions){
		    //save_state = true;
		    ask_for_widgets_state_save();
		    console.log('We arechanging position of'+positions);
		    
		    if($.trim(positions) != ''){
			// Get the widgets places IDs and widgets IDs
			var places = positions.split('|');
			console.log('Places'+places);
			for(var i = 0; i < places.length; i++){
			    // Every part contain a place ID and possible widgets IDs
			    var place = places[i].split('=');
			    // Validate (more or less) the format of the part that must
			    // contain two element: A place ID and one or more widgets IDs
			    if(place.length == 2){
				// Subpart one: the place ID
				var place_name = place[0];
				// Subpart two: one or more widgets IDs
				var widgets = place[1].split(',');
				// Here we have a place and one or more widgets IDs
				for(var j = 0; j < widgets.length; j++){
				    if($.trim(widgets[j]) != ''){
					// So, append every widget in the appropiate place
					var widget_name = widgets[j];
					console.log('Widget and place'+widget_name+' and place '+place_name);
					var w = find_widget(widget_name);
					if(w != -1){
					    // We finally save the new position
					    w.position = place_name;
					}
					console.log('Finded widget'+w);
					//$(widgetSel).appendTo(placeSel);
				    }
				}
			    }
			}
		    }
		    
		    
		},
	    }
	});
    


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

	    //id = w.id;
	    var widget = find_widget(w.id);
	    // Find the widget and check if it was not closed
	    if(widget != -1){
		var o = {'id' : widget.id, 'position' : widget.position, 'base_url' : widget.base_url, 'options' : widget.options, 'collapsed' : widget.collapsed};
		console.log('Saving'+o.collapsed);
		widgets_ids.push(o);
	    }
	});

	console.log('Need to save widgets list'+JSON.stringify(widgets_ids));
	$.post("/user/save_pref", { 'key' : 'widgets', 'value' : JSON.stringify(widgets_ids)});
    }




    setInterval( save_new_widgets, 1000);


});
