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


/* To download, we will ask the skonf daemon to do it,
   and we will show the spinner and hide the button during it
*/
function download_pack(uri, id){
    console.log("We will download the pack at"+uri);
    var spinner = $('#loading-'+id);
    var btn = $('#download-'+id);
    spinner.show();
    btn.button('loading');
    var message = $('#message-'+id);

    $.ajax({
	url: '/download/'+uri,
	dataType: 'json',
	success: function(data) {
            console.log('We get ajax data'+data.state+''+data.text);
	    spinner.hide();
	    btn.button('complete');
	    if(data.state == 200){
		message.addClass('alert-success');

	    }else{
		message.addClass('alert-error');
	    }
	    message.show();
	    message.html(data.text);
        },
        error : function(data) {
            console.log('We get an error ajax call'+data);
	    message.addClass('alert-error');
	    message.show();
	    message.html('Error during the query '+data);
        }
    });

}