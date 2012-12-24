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

new_macro_id = 0;

function add_macro(){
    var s = $('#new_macros');

    var n = $('<form id="new_macro'+new_macro_id+'" class="form-inline"> <input id="new_macro_name_'+new_macro_id+'" class="new_macro_name" name="" type="text" placeholder="new macro"> <input class="new_macro_value offset1" id="new_macro_value_'+new_macro_id+'" name="" type="text" value="" placeholder="value"> <a class="btn btn-danger offset1" href="javascript:del_macro('+new_macro_id+');"><i class="icon-remove"></i> DEL</a> </form> </span>');
    s.append(n);
    new_properties.push(new_macro_id);
    new_macro_id += 1;
}


function del_macro(id){
    var s = $('#new_macro'+id);
    s.hide("slide", { direction: "down" }, 500);
    new_properties.remove(id);
}