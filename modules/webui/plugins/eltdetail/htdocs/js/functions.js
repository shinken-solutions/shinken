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

/* Now a function for managingthe hovering of the problems. Will make
   appears the actiosn buttons with a smoot way (opacity)*/

window.addEvent('domready', function() {
    var status = {
        'true': 'open',
        'false': 'close'
    };
    // -- vertical
    var myVerticalSlide = new Fx.Slide('gesture_slide').hide();

    $('v_toggle').addEvent('click', function(event){
        event.stop();
        myVerticalSlide.toggle();
    });

});
