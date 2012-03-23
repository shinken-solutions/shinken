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

/* We can't apply Jcrop on ready. Why? Because the images are not load, and so
   they wil have a 0 size. Yes, ti's stupid I know. So hjow to do it?
   The key is to hook the graph tab. onshow will raise when we active it (and was shown).
   So we apply only then. Cool isn't it?
   PS : I lost 2 hours in this, and yes, I'm quite angry about this stupid thing....
*/

zoomstart=0;
zoomend=0;

offset=50;
offset_end=25;

function update_coords(c)
{
    
    // variables can be accessed here as
    // c.x, c.y, c.x2, c.y2, c.w, c.h
    zoomstart=Math.max(0, c.x - offset);
    zoomend=Math.min(587, c.x2 - offset_end);
};



// ARG, I'm lost! please don'ttry this, it's buggy as hell. The next tme I do like always
// IE: draw a diag and code after...
// PS: but at least the main idea is working :p

function zoom(uri){
    var original_diff = graphend - graphstart;
    // From now we assume PNP graphs. Should find a generic way here
    
    ratio = (zoomend - zoomstart) / (587 - (offset + offset_end));
    
    alert('Zoom end' + zoomend);
    if(ratio > 1){
	return;
    }
    alert('Ratio is' + ratio+ 'original diff was ' + original_diff);

    var time_ahead = original_diff * (1 - ratio);
    var time_backward = original_diff 

    var new_graphstart = parseInt(graphstart + time_ahead);
    var new_graphend = parseInt(graphend - original_diff * (1-ratio));
    //alert('Start'+graphstart+' came to '+ new_graphstart);
    var new_uri = uri+'graphstart='+new_graphstart+'&graphend='+new_graphend+'#graphs';
    window.location=new_uri;
}

$(window).ready(function(){
    $('#tab_to_graphs').on('shown', function (e) {
	$('.jcropelt').Jcrop({
	    onSelect: update_coords,
            onChange: update_coords
	});
    })
});
