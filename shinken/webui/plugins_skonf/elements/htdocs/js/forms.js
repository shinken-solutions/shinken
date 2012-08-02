/*Copyright (C) 2009-2012 :
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

function form_success(){
    console.log('Form send in success mode');
    var l = $('#saving_log');
    l.show();
    l.removeClass('alert-error');
    l.addClass('alert-success');
    l.html('The host was saved sucessfully. You will be redirected to the host list.');
    var table = $(document.forms['form-element']).attr('data-table');
    setTimeout("location.assign('/elements/"+table+"');", 1000);

}

function form_error(){
    console.log('Form send in error mode');
    var l = $('#saving_log');
    l.show();
    l.removeClass('alert-success');
    l.addClass('alert-error');
    l.html('Error during the host save.');

}


function submit_form(){
    var f = document.forms['form-element'];
    var table = $(f).attr('data-table');
    var _id = f['_id'].value;
    console.log("submiting form"+f);
    console.log('Dump properties'+dump(properties));


    // Get all new properties too
    $.each(new_properties, function(idx, id){
	var input_name = $('#new_macro_name_'+id);
	var input_value = $('#new_macro_value_'+id);
	var name = input_name.val();
	var value = input_value.val();

	console.log('Get new macro'+name+' '+value);
	// Don't want void new macro
	if(name != ''){
	    // It's a macro, it need to start with _
	    // And in upper case
	    if(name[0] != '_'){
		name = '_'+name;
	    }
	    name = name.toUpperCase();
	    // Set the value input with the good name
	    input_value.attr('name', name);
	    // And add this one in the properties list
	    // so we will really save it
	    //console.log('SAving new macro'+dump({'name' : name, 'type' : 'string'}))
	    properties.push({'name' : name, 'type' : 'string'});
	}
    });

    // Sample for bool: $('button[name="process_perf_data"].active').val();
    console.log('Dump process_perf_data'+ $('button[name="process_perf_data"].active').val());
    var res = {};
    $.each(properties, function(idx, prop){
	var name = prop['name'];
	var type = prop['type']
	console.log('Look at'+idx+' '+name+' '+type);
	// Now get the value
	var value = '';
	// String are easy to manage
	if(type == 'string' || type == 'select'){
	    value = f[name].value;
	    console.log('Got value'+value);
	}
	if(type == 'bool'){
	    // For bool we will have '0' '1' or ''
	    value = $('button[name="'+name+'"].active').val();
            console.log('Got bool value'+value);
	}
	if(type == 'percent'){
            // For percent we should look at the lider value
            slider_value = $('#slider_'+name).attr('data-value');
	    is_active = $('#slider_'+name).attr('data-active');
	    if(is_active == '1'){
		console.log('Got percent value'+value);
		value = slider_value;
	    }else{
		console.log('Got default percent value');
		value = '';
	    }
        }
	if(type == 'multiselect'){
	    var s = f[name];
	    var i = 0;
	    var temp_values = [];
            for (i=0;i<s.length;i++){
		if (s[i].selected){
		    console.log('Find multiselect value'+s[i].value);
		    temp_values.push(s[i].value);
		}
            }
	    value = temp_values.join(',');
	    console.log('Got multiselect value'+value);
	}
	if(type == 'command'){
	    // Get the command name is easy
	    var command_name = f[name].value;
	    // Now get the args
	    var args = f['args-'+name].value;
	    value = command_name;
	    if (args != ''){
		// Maybe the use forget the first '!', we add it for him
		if(args[0] != '!'){
		    args = '!'+args;
		}
		value += args;
	    }
	    console.log('Get a command value'+value);
	}
	if(type == 'use_tags'){
	    value = get_use_values(name);
	    console.log('Get a use tag value'+value);
	}
	res[name] = value;
    });
    console.log('Dump data to send'+dump(res));
    $.post('/element/q/'+table+'/save/'+_id, res).success(form_success).error(form_error);
}
