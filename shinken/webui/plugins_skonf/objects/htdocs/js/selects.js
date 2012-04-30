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


$(document).ready(function() {
    $("select[multiple]").bsmSelect(
	{
            showEffect: function($el){ $el.fadeIn(); },
            hideEffect: function($el){ $el.fadeOut(function(){ $(this).remove();}); },
            plugins: [$.bsmSelect.plugins.sortable()],
            title: 'Add',
            highlight: 'highlight',
            addItemTarget: 'original',
            removeLabel: '<span class="token-input-delete-token-facebook">x</span>',
            containerClass: 'bsmContainer span9', // Class for container that wraps this widget
            listClass: 'token-input-list-facebook span8', //bsmList-custom', // Class for the list ($ol)
            listItemClass: 'token-input-token-facebook', // bsmListItem-custom', // Class for the <li> list items
            listItemLabelClass: 'bsmListItemLabel-custom', // Class for the label text that appears in list items
            selectClass : 'bsmSelect span3',
            removeClass: 'bsmListItemRemove-custom' // Class given to the "remove" link
	    //extractLabel: function($o) {return $o.parents('optgroup').attr('label') + "&nbsp;>&nbsp;" + $o.html();}
	}
    );
    
});

