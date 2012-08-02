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

// At start, hide the service lists
$(document).ready(function(){
    $('#pass_ok').hide();
    $('#pass_bad').hide();
    $('#message').hide();
});


function check_pass_match(){
    var f = document.forms['user'];
    var pwd = f.password.value;
    var pwd2 = f.password2.value;
    console.log('Passwords'+pwd+' and '+pwd2);
    if (pwd != pwd2){
	$('#pass_ok').hide();
	$('#pass_bad').show();
    }else{
	$('#pass_ok').show();
	$('#pass_bad').hide();
    }
}

function submit_user_error(){
    console.log('Sorry there is an error');
    var m = $('#message');
    m.show();
    m.removeClass('alert-success');
    m.addClass('alert-error');
    m.html('Sorry there was an error in your query');

}

function submit_user_ok(){
    console.log('OK');
    var m = $('#message');
    m.show();
    m.addClass('alert-success');
    m.removeClass('alert-error');
    m.html('Account update OK');

}


function submit_user_form(){
    var f = document.forms['user'];
    var pwd = f.password.value;
    var pwd2 = f.password.value;
    var email = f.email.value;
    $.ajax({
	type: 'POST',
	url: '/user',
	data: {password : pwd, password2: pwd2, email: email},
	success: submit_user_ok,
	error : submit_user_error
    });
}