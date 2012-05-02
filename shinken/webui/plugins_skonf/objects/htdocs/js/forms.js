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




function submit_form(){
    var f = document.forms['form-host'];
    var _id = f['_id'].value;
    console.log("submiting form"+f);
    console.log('Dump properties'+dump(properties));
    
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
    $.post('/object/q/hosts/save/'+_id, res);

}
