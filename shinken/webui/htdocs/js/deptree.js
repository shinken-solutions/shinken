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




/* The business rules toggle buttons*/
function toggleBusinessElt(e) {
    //alert('Toggle'+e);
    var toc = document.getElementById('business-parents-'+e);
    var imgLink = document.getElementById('business-parents-img-'+e);
    
    img_src = '/static/images/';

    if (toc && toc.style.display == 'none') {
	toc.style.display = 'block';
	if (imgLink != null){
	    imgLink.src = img_src+'reduce.png';
	}
    } else {
	toc.style.display = 'none';
	if (imgLink != null){
	    imgLink.src = img_src+'expand.png';
	}
    }
}

