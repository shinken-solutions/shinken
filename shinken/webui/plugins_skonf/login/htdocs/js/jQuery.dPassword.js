/*******************************************************************************
 * dPassword v0.1 - jQuery delayed password masking (iPhone style)
 *
 * licensed under MIT License
 *
 * Copyright (c) 2009 DECAF�, Stefan Ullrich (http://decaf.de)
 *
 * Permission is hereby granted, free of charge, to any person obtaining 
 * a copy of this software and associated documentation files (the "Software"), 
 * to deal in the Software without restriction, including without limitation 
 * the rights to use, copy, modify, merge, publish, distribute, sublicense, 
 * and/or sell copies of the Software, and to permit persons to whom the 
 * Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be 
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, 
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES 
 * OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
 * IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, 
 * DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR 
 * OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR 
 * THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 *
 * Known Issues: - delete marked text will not work
 *               - deleting a single chars will not work if char is 
 *                 not the last char
 *               - view will not follow cursor if textfield is too small
 *               - if id based styles are assigned, these styles will 
 *                 not be taken over
 *
 *******************************************************************************/

(function($){
   $.fn.dPassword = function(options) {

      var defaults = {
         interval:      200,
         duration:      500,
         replacement:   '%u25CF',
         prefix:        'password_',
         debug:  	false
      }

      var opts    = $.extend(defaults, options);
      var checker = new Array();
      var timer   = new Array();

      $(this).each(function() {
         if (opts.debug) console.log('init [' + $(this).attr('id') + ']');

         // get original password tag values
         var name        = $(this).attr('name');
         var id          = $(this).attr('id');
         var cssclass    = $(this).attr('class');
         var style       = $(this).attr('style');
         var size        = $(this).attr('size');
         var maxlength   = $(this).attr('maxlength');
         var disabled    = $(this).attr('disabled');
         var tabindex    = $(this).attr('tabindex');
         var accesskey   = $(this).attr('accesskey');
         var value       = $(this).attr('value');

         // set timers
         checker.push(id);
         timer.push(id);

         // hide field
         $(this).hide();
         
         // add debug span
         if (opts.debug) {
				$(this).after('<span id="debug_' + opts.prefix + name + '" style="color: #f00;"></span>');         
         }
         // add new text field
         $(this).after(' <input name="' + (opts.prefix + name) + '" ' +
                                 'id="' +  (opts.prefix + id) + '" ' + 
                               'type="text" ' +
                              'value="' + value + '" ' +
               (cssclass != '' ? 'class="' + cssclass + '"' : '') +
               (style != '' ? 'style="' + style + '"' : '') +
                 (size != '' ? 'size="' + size + '"' : '') +
       (maxlength != -1 ? 'maxlength="' + maxlength + '"' : '') +
         //(disabled != '' ? 'disabled="' + disabled + '"' : '') +
         (tabindex != '' ? 'tabindex="' + tabindex + '"' : '') +
 (accesskey != undefined ? 'accesskey="' + accesskey + '"' : '') +
                      'autocomplete="off" />');
         
         // change label
         $('label[for='+id+']').attr('for', opts.prefix + id);
         // disable tabindex
         $(this).attr('tabindex', '');
         // disable accesskey
         $(this).attr('accesskey', '');


         // bind event
         $('#' + opts.prefix + id).bind('focus', function(event) {
            if (opts.debug) console.log('event: focus [' + getId($(this).attr('id')) + ']');
            clearTimeout(checker[getId($(this).attr('id'))]);
            checker[getId($(this).attr('id'))] = setTimeout("check('" + getId($(this).attr('id')) + "', '')", opts.interval);
         });
         $('#' + opts.prefix + id).bind('blur', function(event) {
            if (opts.debug) console.log('event: blur [' + getId($(this).attr('id')) + ']');
            clearTimeout(checker[getId($(this).attr('id'))]);
         });

			setTimeout("check('" + id + "', '', true);", opts.interval);
      });

      getId = function(id) {
         var pattern = opts.prefix+'(.*)';
         var regex = new RegExp(pattern);
         regex.exec(id);
         id = RegExp.$1;
         
         return id;
      }
   
      setPassword = function(id, str) {
         if (opts.debug) console.log('setPassword: [' + id + ']');

         var tmp = '';
         for (i=0; i < str.length; i++) {
            if (str.charAt(i) == unescape(opts.replacement)) {
               tmp = tmp + $('#' + id).val().charAt(i);
            }
            else {
               tmp = tmp + str.charAt(i);
            }
         }
         $('#' + id).val(tmp);
      }
      
      check = function(id, oldValue, initialCall) {
         if (opts.debug) console.log('check: [' + id + ']');
         
         var bullets = $('#' + opts.prefix + id).val();

         if (oldValue != bullets) {
            setPassword(id, bullets);
            if (bullets.length > 1) {
               var tmp = '';
               for (i=0; i < bullets.length-1; i++) {
                  tmp = tmp + unescape(opts.replacement);
               }
               tmp = tmp + bullets.charAt(bullets.length-1);
   
               $('#' + opts.prefix + id).val(tmp);
            }
            else {
            }
            clearTimeout(timer[id]);
            timer[id] = setTimeout("convertLastChar('" + id + "')", opts.duration);
         }
         if (opts.debug) {
         	$('#debug_' + opts.prefix + id).text($('#' + id).val());
         }
         if (!initialCall) {
	         checker[id] = setTimeout("check('" + id + "', '" + $('#' + opts.prefix + id).val() + "', false)", opts.interval);
			}
      }
      
      convertLastChar = function(id) {
         if ($('#' + opts.prefix + id).val() != '') {
            var tmp = '';
            for (i=0; i < $('#' + opts.prefix + id).val().length; i++) {
               tmp = tmp + unescape(opts.replacement);
            }
   
            $('#' + opts.prefix + id).val(tmp);
         }
      }
   };
}) (jQuery);

