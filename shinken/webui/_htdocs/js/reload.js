/*Copyright (C) 2009-2011 :
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


/* By default, we set the page to reload each 60s*/
var refresh_timeout = 60;

/* Each second, we check for timeout and restart page */
function check_refresh(){
    if(refresh_timeout < 0){
	location.assign(location.href);
    }
    refresh_timeout = refresh_timeout - 1;    
}


/* Someone ask us to reinit the refresh so the user will have time to
   do some thigns like ask actions or something like that */
function reinit_refresh(){
    refresh_timeout = 60;
}

/* We will check timeout each 1s*/
window.addEvent('domready', function(){
	setInterval("check_refresh();", 1000); 
    });

