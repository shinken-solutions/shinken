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



/*
  For the tags list, we are adding span with image and text. The image
  can be a 404, so we catch it and remove the image.
*/

function create_img(src){
    var img = $("<img/>");

    // If we got problem with the image, bail out the
    // print/ WARNING : BEFORE set src!
    img.error(function() {
	$(this).hide()
    });

    //src = '/static/images/state_down.png';
    img.addClass('imgsize2')
    img.attr('src', src);

    return img;
}

// First we look for the img_hover div and we add it
// the image, and we set it in the good place
function add_tag_image(src, name){
    var img = create_img(src, name);
    var span = $("<span/>");
    var a = $('<a href="/all?search=htag:'+name+'"/>');
    span.addClass('label');


    span.append(img);
    span.append(''+name);
    // And put the whole in the tag list
    a.append(span);
    $('#host_tags').append(a);
}
