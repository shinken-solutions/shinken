/*
 * Better Select Multiple Compatibility Plugin - jQuery Plugin
 *
 * Copyright (c) 2010 by Victor Berchet - http://www.github.com/vicb
 *
 * Dual licensed under the MIT (MIT-LICENSE.txt) and GPL (GPL-LICENSE.txt) licenses.
 *
 * version: v1.0.1 - 2011-11-14
 */
(function($) {
  $.bsmSelect.plugins.compatibility = function()
  {
    if (!(this instanceof $.bsmSelect.plugins.compatibility)) {
      return new $.bsmSelect.plugins.compatibility();
    }
  }

  $.extend($.bsmSelect.plugins.compatibility.prototype, {
    init: function(bsm) {

      var o = bsm.options;

      if (typeof o.animate != 'undefined')
      {
        if (o.animate === true) {
          o.showEffect = $.bsmSelect.effects.verticalListAdd;
          o.hideEffect = $.bsmSelect.effects.verticalListRemove;
        } else if ($.isFunction(o.animate.add)) {
          o.showEffect = o.animate.add;
        } else if (typeof(o.animate.add) == 'string' && $.isFunction($.bsmSelect.effects[o.animate.add])) {
          o.showEffect = $.bsmSelect.effects[o.animate.add];
        } else {
          o.showEffect = $.bsmSelect.effects.show;
        }

        if ($.isFunction(o.animate.drop)) {
          o.hideEffect = o.animate.drop;
        } else if (typeof(o.animate.drop) == 'string' && $.isFunction($.bsmSelect.effects[o.animate.drop])) {
          o.hideEffect = $.bsmSelect.effects[o.animate.drop];
        } else {
          o.hideEffect = $.bsmSelect.effects.remove;
        }
      }

      if (typeof o.highlight != 'undefined')
      {
        if (o.highlight === true) {
          o.highlightEffect = $.bsmSelect.effects.highlight;
        } else if ($.isFunction(o.highlight)) {
          o.highlightEffect = o.highlight;
        } else if (typeof(o.highlight) == 'string' && $.isFunction($.bsmSelect.effects[o.highlight])) {
          o.highlightEffect = $.bsmSelect.effects[o.highlight];
        }
      }

    }

  });
})(jQuery);

