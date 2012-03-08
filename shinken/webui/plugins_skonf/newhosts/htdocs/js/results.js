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




function validatehostform(name) {
    //var form = document.forms[name];//.submit();

    var form = $("form-"+name);
    //alert("submit" + name);
    /**
     * This empties the log and shows the spinning indicator
     */
    var log = $("res-"+name).empty().addClass('ajax-loading');

    new Request({
        method: form.method,
        url: form.action+"toto",
        onSuccess: function(responseText, responseXML) {
            log.removeClass('ajax-loading');
            log.set('text', 'text goes here');
	    div_res = $("good-result-"+name);
	    new Fx.Slide(div_res).show();
	    div_res.highlight('#ddf');
        },
	onFailure: function(responseText, responseXML) {
            log.removeClass('ajax-loading');
            log.set('text', 'ajax finished');
	    div_res = $("bad-result-"+name);
	    new Fx.Slide(div_res).show();
	    div_res.highlight('#ddf');
        }

    }).send(form.toQueryString());
}




/* We Hide all results divs */
window.addEvent('domready', function(){
    var res = $$('.div-result');
	 res.each(function(el){
	     new Fx.Slide(el).hide();
	 });
});
