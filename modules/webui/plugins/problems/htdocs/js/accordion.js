/*Copyright (C) 2009-2011 :
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


/* We Hide all detail elements */
$(document).ready(function(){
    var details = $('.detail');
    details.hide();

    // By default hide all "hide" chevron of the right part
    $('.chevron-up').hide();
});


/*
  Look for Shift key up and down
*/
is_shift_pressed = false;
function shift_pressed(){
    is_shift_pressed = true;
}

function shift_released(){
    is_shift_pressed = false;
}

$(document).bind('keydown', 'shift', shift_pressed);
$(document).bind('keyup', 'shift', shift_released);

/*
  If we keep the shift pushed and hovering over selections, it
  select the elements. Easier for massive selection :)
*/
function hovering_selection(name){
    if(is_shift_pressed){
	add_element(name);
    }
}


/*
  Tool bar related code
*/

function hide_toolbar(){
    $('#toolbar').hide();
    $('#hide_toolbar_btn').hide();
    $('#show_toolbar_btn').show();
    save_toolbar('hide');
}

function show_toolbar(){
    $('#toolbar').show();
    $('#hide_toolbar_btn').show();
    $('#show_toolbar_btn').hide();
    save_toolbar('show');
}

function save_toolbar(toolbar){
    console.log('Need to save toolbar pref '+toolbar);
    $.post("/user/save_pref", { 'key' : 'toolbar', 'value' : toolbar});
}



/* And if the user lick on the good image, we untoggle them. */
function show_detail(name){
    var myFx = $('#'+name).slideToggle();
    $('#show-detail-'+name).toggle();
    $('#hide-detail-'+name).toggle();
}


// The user ask to show the hidden problems that are duplicated
function show_hidden_problems(cls){
    $('.'+cls).show();
    // And hide the vvv button
    $('#btn-'+cls).hide();
}

// At start we hide the unselect all button
$(document).ready(function(){
    $('#unselect_all_btn').hide();
    if(toolbar_hide){
        hide_toolbar();
    }else{
        $('#show_toolbar_btn').hide();
    }

    // If actions are not allowed, disable the button 'select all'
    if(!actions_enabled){
	$('#select_all_btn').addClass('disabled');
	// And put in opacity low the 'selectors'
	$('.tick').css({'opacity' : 0.4});
    }
});


// At start we hide the selected images
// and the actions tabs
$(document).ready(function(){
    $('.img_tick').hide();
    $('#actions').hide();
});



function toggle_select_buttons(){
    $('#select_all_btn').toggle();
    $('#unselect_all_btn').toggle();
}

function show_unselect_all_button(){
    $('#select_all_btn').hide();
    $('#unselect_all_btn').show();
}

function show_select_all_button(){
    $('#unselect_all_btn').hide();
    $('#select_all_btn').show();
}

// When we select all, add all in the selected list,
// and hide the select all button, and swap it with
// unselect all one
function select_all_problems(){
    // Maybe the actions are not allwoed. If so, don't act
    if(!actions_enabled){return;}

    toggle_select_buttons();
    /*$('#select_all_btn').hide();
    $('#unselect_all_btn').show();*/

    // we wil lget all elements by looking at .details and get their ids
    $('.detail').each(function(){
	add_element($(this).attr('id'));
    });
}

// guess what? unselect is the total oposite...
function unselect_all_problems(){
    toggle_select_buttons();
    /*$('#unselect_all_btn').hide();
    $('#select_all_btn').show();*/
    flush_selected_elements();
}


/* We keep an array of all selected elements */
var selected_elements = [];

function add_remove_elements(name){
    // Maybe the actions are not allwoed. If so, don't act
    if(!actions_enabled){return;}


    //alert(selected_elements.indexOf(name));
    if( selected_elements.indexOf(name) != -1 ){
	remove_element(name);
    }else{
	add_element(name);
    }
}


/* function when we add an element*/
function add_element(name){
    selected_elements.push(name);

    // We put the select all button in unselect mode
    show_unselect_all_button();

    // We show the 'tick' image ofthe selector on the left
    $('#selector-'+name).show();

    $('#actions').show();
    /*$('#actions').css('display', 'block');
    $('#actions').animate({opacity:1});*/
    /* The user will ask something, so it's good to reinit
     the refresh time so he got time to launch its action,
    see reload.js for this function */
    reinit_refresh();
}

/* And or course when we remove it... */
function remove_element(name){
    selected_elements.remove(name);
    if(selected_elements.length == 0){
	$('#actions').hide();
	show_select_all_button();
	/*$('#actions').animate({opacity:0});
	$('#actions').css('display', 'none');*/
    }
    // And hide the tick image
    $('#selector-'+name).hide();
}


/* Flush selected elements, so clean the list
but also untick thems in the UI */
function flush_selected_elements(){
    /* We must copy the list so we can parse it in a clean way
     without fearing some bugs */
    var cpy = $.extend({}, selected_elements);
    $.each(cpy, function(idx, name) {
	remove_element(name);
    });
}


/* Jquery need simple id, so no / or space. So we get in the #id
the data-raw-obj-name to get the unchanged name*/
function unid_name(name){
    return $('#'+name).attr('data-raw-obj-name');
}

/* Now actions buttons : */
function recheck_now_all(){
    $.each(selected_elements,function(idx, name){
	recheck_now(unid_name(name));
    });
    flush_selected_elements();
}


/* Now actions buttons : */
function try_to_fix_all(){
    $.each(selected_elements, function(idx, name){
        try_to_fix(unid_name(name));
    });
    flush_selected_elements();
}


function acknowledge_all(user){
    $.each(selected_elements, function(idx, name){
	do_acknowledge(unid_name(name), 'Acknowledged from WebUI by '+user, user);
    });
    flush_selected_elements();
}


function remove_all(user){
    $.each(selected_elements, function(idx, name){
        do_remove(unid_name(name), 'Removed from WebUI by '+user, user);
    });
    flush_selected_elements();
}
