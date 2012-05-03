/*
 * Better Select Multiple Sortable Plugin
 *
 * Copyright (c) 2010 by Victor Berchet - http://www.github.com/vicb
 *
 * Dual licensed under the MIT (MIT-LICENSE.txt) and GPL (GPL-LICENSE.txt) licenses.
 *
 * version: v1.4.4 - 2012-01-19
 */
(function($) {
  $.bsmSelect.plugins.sortable = function(sortConfig, options)
  {
    if (!(this instanceof $.bsmSelect.plugins.sortable)) {
      return new $.bsmSelect.plugins.sortable(sortConfig, options);
    }
    this.sortConfig = sortConfig;
    this.options = $.extend({}, this.defaultOpt, options || {});
  }

  $.extend($.bsmSelect.plugins.sortable.prototype, {
    defaultOpt: {
      listSortableClass:  'bsmListSortable'
    },

    init: function(bsm) {
      var o = $.extend({}, this.options, bsm.options),
        config = $.extend({}, this.sortConfig, { items: '.' + o.listItemClass }),
        self = this;
      bsm.$list.addClass(o.listSortableClass).sortable(config);
      // Fix a bug when the 'html' element has an overflow set to either 'scroll' or 'auto' on FF.
      // See issue #21 (https://github.com/vicb/bsmSelect/issues/21)
      if ($.inArray($('html').css('overflow-x'), ['auto', 'scroll']) > -1 || $.inArray($('html').css('overflow-y'), ['auto', 'scroll']) > -1) {
        $('.' + o.listSortableClass).addClass('bsmScrollWorkaround');
      }
      bsm.$original.bind('change', function(e, info) { self.onChange.call(self, bsm, e, info); } );
      bsm.$list.bind('sortupdate', function(e, ui) { self.onSort.call(self, bsm, e, ui); } );
    },

    onChange: function(bsm, e, info) {
      if (info && info.type === 'add' && !bsm.buildingSelect) {
        info.option.detach()[bsm.options.addItemTarget === 'top' ? 'prependTo' : 'appendTo'](bsm.$original);
        bsm.$list.sortable('refresh');
      }
    },

    onSort: function(bsm, e, ui) {
      $('.' + bsm.options.listItemClass, bsm.$list).each(function() {
        $(this).data('bsm-option').data('orig-option').detach().appendTo(bsm.$original);
      });
      bsm.triggerOriginalChange($(ui.item).data('bsm-option').data('orig-option'), 'sort');
    }
  });
})(jQuery);
