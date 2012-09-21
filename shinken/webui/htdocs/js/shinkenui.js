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

/***************************************************************************/

/**
 * Some browser do NOT have indexOf for arrays... so we add it!
**/
if(!Array.indexOf){
    Array.prototype.indexOf = function(obj){
	for(var i=0; i<this.length; i++){
	    if(this[i]==obj){
		return i;
	    }
	}
	return -1;
    }
}

/**
 * Description: Add a remvoe finction to the lists....
 *  WTF javascript don't have this? Please guys, at least good
 *  list and dict functions.... you want us to manage memory soon?
 * Example: lst.remove(value)
 */
Array.prototype.remove=function(s){
    var index = this.indexOf(s);
    while(this.indexOf(s) != -1){
	this.splice(index, 1);
	index = this.indexOf(s);
    }
}



/**
 * Description:
 * Example: <div class="pulsate"> <p> Example DIV </p> </div>
 */

$(function() {
  var p = $(".pulsate");
  for(var i=0; i<5; i++) {
    p.animate({opacity: 0.2}, 1000, 'linear')
     .animate({opacity: 1}, 1000, 'linear');
  }
});

/**
 * Description:
 * Example: <a rel="tooltip" href="#" data-original-title="Lorem Ipsum">Lorem Ipsum</a>
 */

$(function(){
    $('a[rel=tooltip]').tooltip();
    $('tr[rel=tooltip]').tooltip();
    $('td[rel=tooltip]').tooltip();
});

/**
 * Description:
 * Example: <div class="quickinfo"> Lorem Ipsum </div>
 */

$(function(){
    $(".quickinfo").tooltip({placement: 'bottom'});
});

/**
 * Description:
 * Example: <div class="quickinfo"> Lorem Ipsum </div>
 */

$(function(){
    $(".quickinforight").tooltip({placement: 'right'});
});

/*
 * How to code whithout a good print function?
 */

function dump(arr,level) {
    var dumped_text = "";
    if(!level) level = 0;

    //The padding given at the beginning of the line.
    var level_padding = "";
    for(var j=0;j<level+1;j++) level_padding += "    ";

    if(typeof(arr) == 'object') { //Array/Hashes/Objects
	for(var item in arr) {
	    var value = arr[item];

	    if(typeof(value) == 'object') { //If it is an array,
		dumped_text += level_padding + "'" + item + "' ...\n";
		dumped_text += dump(value,level+1);
	    } else {
		dumped_text += level_padding + "'" + item + "' => \"" + value + "\"\n";
	    }
	}
    } else { //Stings/Chars/Numbers etc.
	dumped_text = "===>"+arr+"<===("+typeof(arr)+")";
    }
    return dumped_text;
}

/*
 * To load on run some additonnal js or css files.
*/
function loadjscssfile(filename, filetype){
 if (filetype=="js"){ //if filename is a external JavaScript file
  var fileref=document.createElement('script')
  fileref.setAttribute("type","text/javascript")
  fileref.setAttribute("src", filename)
 }
 else if (filetype=="css"){ //if filename is an external CSS file
  var fileref=document.createElement("link")
  fileref.setAttribute("rel", "stylesheet")
  fileref.setAttribute("type", "text/css")
  fileref.setAttribute("href", filename)
 }
 if (typeof fileref!="undefined")
  document.getElementsByTagName("head")[0].appendChild(fileref)
}

/**
 * Description:
 * Example: <div class="truncate"> Lorem Ipsum </div>
 */

(function($){
    $.fn.jTruncate = function(options) {
       
        var defaults = {
            length: 300,
            minTrail: 20,
            moreText: "more",
            lessText: "less",
            ellipsisText: "...",
            moreAni: "",
            lessAni: ""
        };
        
        var options = $.extend(defaults, options);
       
        return this.each(function() {
            obj = $(this);
            var body = obj.html();
            
            if(body.length > options.length + options.minTrail) {
                var splitLocation = body.indexOf(' ', options.length);
                if(splitLocation != -1) {
                    // truncate tip
                    var splitLocation = body.indexOf(' ', options.length);
                    var str1 = body.substring(0, splitLocation);
                    var str2 = body.substring(splitLocation, body.length - 1);
                    obj.html(str1 + '<span class="truncate_ellipsis">' + options.ellipsisText +
                        '</span>' + '<span class="truncate_more">' + str2 + '</span>');
                    obj.find('.truncate_more').css("display", "none");
                    
                    // insert more link
                    obj.append(
                        '<div class="clearboth">' +
                            '<a href="#" class="truncate_more_link">' + options.moreText + '</a>' +
                        '</div>'
                    );

                    // set onclick event for more/less link
                    var moreLink = $('.truncate_more_link', obj);
                    var moreContent = $('.truncate_more', obj);
                    var ellipsis = $('.truncate_ellipsis', obj);
                    moreLink.click(function() {
                        if(moreLink.text() == options.moreText) {
                            moreContent.show(options.moreAni);
                            moreLink.text(options.lessText);
                            ellipsis.css("display", "none");
                        } else {
                            moreContent.hide(options.lessAni);
                            moreLink.text(options.moreText);
                            ellipsis.css("display", "inline");
                        }
                        return false;
                      });
                }
            } // end if
            
        });
    };
})(jQuery);


/**
 * Description: Url changer
 * Example: header_element.tpl
 */

function skonf() {
    var Port = 7766;
    var Host = document.domain;
    var Url = 'http://' + Host + ':' + Port;
    return Url;
}

function webui() {
    var Port = 7767;
    var Host = document.domain;
    var Url = 'http://' + Host + ':' + Port;
    return Url;
}

$(function(){
    $("a[href=':7766']").attr('href', skonf());
    $("a[href=':7767']").attr('href', webui());
});
