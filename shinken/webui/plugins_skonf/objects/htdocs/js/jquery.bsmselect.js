/*
 * Better Select Multiple - jQuery Plugin
 *
 * based on Alternate Select Multiple (asmSelect) 1.0.4a beta (http://www.ryancramer.com/projects/asmselect/)
 *
 * Copyright (c) 2009 by Ryan Cramer - http://www.ryancramer.com
 * Copyright (c) 2010 by Victor Berchet - http://www.github.com/vicb
 *
 * Dual licensed under the MIT (MIT-LICENSE.txt) and GPL (GPL-LICENSE.txt) licenses.
 *
 * bsmSelect version: v1.4.3 - 2011-05-05
 */

(function($) {

  function BsmSelect(target, options)
  {
    this.$original = $(target);             // the original select multiple
    this.buildingSelect = false;            // is the new select being constructed right now?
    this.ieClick = false;                   // in IE, has a click event occurred? ignore if not
    this.ignoreOriginalChangeEvent = false; // originalChangeEvent bypassed when this is true
    this.options = options;
    this.buildDom();
  }

  BsmSelect.prototype = {
    /**
     * Generate an UID
     */
    generateUid: function(index) {
      return (this.uid = this.options.containerClass + index);
    },

    /**
     * Build the DOM for bsmSelect
     */
    buildDom: function() {
      var self = this, o = this.options;

      if (o.addItemTarget === 'original') {
        $('option', this.$original).each(function(i, o) {
          if ($(o).data('bsm-order') === null) { $(o).data('bsm-order', i); }
        });
      }

      for (var index = 0; $('#' + this.generateUid(index)).size(); index++) {}

      this.$select = $('<select>', {
        'class': o.selectClass,
        name: o.selectClass + this.uid,
        id: o.selectClass + this.uid,
        change: $.proxy(this.selectChangeEvent, this),
        click: $.proxy(this.selectClickEvent, this)
      });

      this.$list = $.isFunction(o.listType)
        ? o.listType(this.$original)
        : $('<' + o.listType + '>', { id: o.listClass + this.uid });

      this.$list.addClass(o.listClass);

      this.$container = $('<div>', { 'class':  o.containerClass, id: this.uid });

      this.buildSelect();

      this.$original.change($.proxy(this.originalChangeEvent, this)).wrap(this.$container).before(this.$select);

      // if the list isn't already in the document, add it (it might be inserted by a custom callback)
      if (!this.$list.parent().length) { this.$original.before(this.$list); }

      if (this.$original.attr('id')) {
        $('label[for=' + this.$original.attr('id') + ']').attr('for', this.$select.attr('id'));
      }

      // set up remove event (may be a link, or the list item itself)
      this.$list.delegate('.' + o.removeClass, 'click', function() {
        self.dropListItem($(this).closest('li'));
        return false;
      });

      $.each(o.plugins, function() { this.init(self); });
    },

    /**
     * Triggered when an item has been selected
     * Check to make sure it's not an IE screwup, and add it to the list
     */
    selectChangeEvent: function() {
      if ($.browser.msie && $.browser.version < 7 && !this.ieClick) { return; }
      var bsmOpt = $('option:selected:eq(0)', this.$select);
      if (bsmOpt.data('orig-option')) {
        this.addListItem(bsmOpt);
        this.triggerOriginalChange(bsmOpt.data('orig-option'), 'add');
      }
      this.ieClick = false;
    },

    /**
     * IE6 lets you scroll around in a select without it being pulled down
     * making sure a click preceded the change() event reduces the chance
     * if unintended items being added. there may be a better solution?
     */
    selectClickEvent: function() {
      this.ieClick = true;
    },

    /**
     * Rebuild bsmSelect when the 'change' event is triggered on the original select
     */
    originalChangeEvent: function() {
      if (this.ignoreOriginalChangeEvent) {
        // We don't want to rebuild everything when an item is added / droped
        this.ignoreOriginalChangeEvent = false;
      } else {
        this.buildSelect();
        // opera has an issue where it needs a force redraw, otherwise
        // the items won't appear until something else forces a redraw
        if ($.browser.opera) { this.$list.hide().show(); }
      }
    },

    /**
     * Build the DOM for the new select
     */
    buildSelect: function() {
      var self = this;

      this.buildingSelect = true;

      // add a first option to be the home option / default selectLabel
      this.$select.empty().prepend($('<option value=""></option>').text(this.$original.attr('title') || this.options.title));
      this.$list.empty();

      this.$original.children().each(function() {
        if ($(this).is('option')) {
          self.addSelectOption(self.$select, $(this));
        } else if ($(this).is('optgroup')) {
          self.addSelectOptionGroup(self.$select, $(this));
        }
      });

      if (!this.options.debugMode) { this.$original.hide(); }
      this.selectFirstItem();
      this.buildingSelect = false;
    },

    /**
     * Append an option to the new select
     *
     * @param {jQuery} $parent Where to append the option
     * @param {jQuery} $origOpt Option from the original select
     */
     addSelectOption: function ($parent, $origOpt) {
     var $bsmOpt = $('<option>', {
        text: $origOpt.text(),
        val: $origOpt.val() }).appendTo($parent).data('orig-option', $origOpt),
      isSelected = $origOpt.is(':selected'),
      isDisabled = $origOpt.is(':disabled');
      $origOpt.data('bsm-option', $bsmOpt);
      if (isSelected && !isDisabled) {
        this.addListItem($bsmOpt);
        this.disableSelectOption($bsmOpt);
      } else if (!isSelected && isDisabled) {
        this.disableSelectOption($bsmOpt);
      }
    },

    /**
     * Append an option group to the new select
     *
     * @param {jQuery} $parent Where to append the group
     * @param {jQuery} $group  Model group from the original select
     */
    addSelectOptionGroup: function($parent, $group)
    {
      var self = this,
        $G = $('<optgroup>', { label: $group.attr('label')} ).appendTo($parent);
      if ($group.is(':disabled')) { $G.attr('disabled', 'disabled'); }
      $('option', $group).each(function() { self.addSelectOption($G, $(this)); });
    },

    /**
     * Select the first item of the new select
     */
    selectFirstItem: function() {
      $('option:eq(0)', this.$select).attr('selected', 'selected');
    },

    /**
     * Make an option disabled, indicating that it's already been selected
     * because safari is the only browser that makes disabled items look 'disabled'
     * we apply a class that reproduces the disabled look in other browsers
     *
     * @param {jQuery} $bsmOpt Option from the new select
     */
    disableSelectOption: function($bsmOpt) {
      $bsmOpt.addClass(this.options.optionDisabledClass)
        .removeAttr('selected')
        .attr('disabled', 'disabled')
        .toggle(!this.options.hideWhenAdded);
      if ($.browser.msie && $.browser.version < 8) { this.$select.hide().show(); } // this forces IE to update display
    },

    /**
     * Enable a select option
     *
     * @param {jQuery} $bsmOpt Option from the new select
     */
    enableSelectOption: function($bsmOpt) {
      $bsmOpt.removeClass(this.options.optionDisabledClass)
        .removeAttr('disabled')
        .toggle(!this.options.hideWhenAdded);
      if ($.browser.msie && $.browser.version < 8) { this.$select.hide().show(); } // this forces IE to update display
    },

    /**
     * Append an item corresponding to the option to the list
     *
     * @param {jQuery} $bsmOpt Option from the new select
     */
    addListItem: function($bsmOpt) {
      var $item,
        $origOpt = $bsmOpt.data('orig-option'),
        o = this.options;

      if (!$origOpt) { return; } // this is the first item, selectLabel

      if (!this.buildingSelect) {
        if ($origOpt.is(':selected')) { return; } // already have it
        $origOpt.attr('selected', 'selected');
      }

      $item = $('<li>', { 'class': o.listItemClass })
        .append($('<span>', { 'class': o.listItemLabelClass, html: o.extractLabel($bsmOpt, o)}))
        .append($('<a>', { href: '#', 'class': o.removeClass, html: o.removeLabel }))
        .data('bsm-option', $bsmOpt);

      this.disableSelectOption($bsmOpt.data('item', $item));

      switch (o.addItemTarget) {
        case 'bottom':
          this.$list.append($item.hide());
          break;
        case 'original':
          var order = $origOpt.data('bsm-order'), inserted = false;
          $('.' + o.listItemClass, this.$list).each(function() {
            if (order < $(this).data('bsm-option').data('orig-option').data('bsm-order')) {
              $item.hide().insertBefore(this);
              inserted = true;
              return false;
            }
          });
          if (!inserted) { this.$list.append($item.hide()); }
          break;
        default:
          this.$list.prepend($item.hide());
      }

      if (this.buildingSelect) {
        $.bsmSelect.effects.show($item);
      } else {
        o.showEffect($item);
        o.highlightEffect(this.$select, $item, o.highlightAddedLabel, this.options);
        this.selectFirstItem();
      }
    },

    /**
     * Remove an item from the list of selection
     *
     * @param {jQuey} $item A list item
     */
    dropListItem: function($item) {
      var $bsmOpt = $item.data('bsm-option'), o = this.options;
      $bsmOpt.removeData('item').data('orig-option').removeAttr('selected');
      (this.buildingSelect ? $.bsmSelect.effects.remove : o.hideEffect)($item);
      this.enableSelectOption($bsmOpt);
      o.highlightEffect(this.$select, $item, o.highlightRemovedLabel, o);
      this.triggerOriginalChange($bsmOpt.data('orig-option'), 'drop');
    },

    /**
     * Trigger a change event on the original select multiple
     * so that other scripts can pick them up
     *
     * @param {jQuery} $origOpt The option from the original select
     * @param {String} type     Event type
     */
    triggerOriginalChange: function($origOpt, type) {
      this.ignoreOriginalChangeEvent = true;
      this.$original.trigger('change', [{
        option: $origOpt,
        value: $origOpt.val(),
        item: $origOpt.data('bsm-option').data('item'),
        type: type
      }]);
    }
  };

  $.fn.bsmSelect = function(customOptions) {
    var options = $.extend({}, $.bsmSelect.conf, customOptions);
    return this.each(function() {
      var bsm = $(this).data("bsmSelect");
      if (!bsm) {
        bsm = new BsmSelect($(this), options);
        $(this).data("bsmSelect", bsm);
      }
    });
  };

  $.bsmSelect = {};
  $.extend($.bsmSelect, {
    effects: {
      show: function($el) { $el.show(); },

      remove: function($el) { $el.remove(); },

      highlight: function ($select, $item, label, conf) {
        var $highlight,
          id = $select.attr('id') + conf.highlightClass;
        $('#' + id).remove();
        $highlight = $('<span>', {
          'class': conf.highlightClass,
          id: id,
          html: label + $item.children('.' + conf.listItemLabelClass).first().text()
        }).hide();
        $select.after($highlight.fadeIn('fast').delay(50).fadeOut('slow', function() { $(this).remove(); }));
      },

      verticalListAdd: function ($el) {
        $el.animate({ opacity: 'show', height: 'show' }, 100, function() {
          $(this).animate({ height: '+=2px' }, 100, function() {
            $(this).animate({ height: '-=2px' }, 100);
          });
        });
      },

      verticalListRemove: function($el) {
        $el.animate({ opacity: 'hide', height: 'hide' }, 100, function() {
          $(this).prev('li').animate({ height: '-=2px' }, 100, function() {
            $(this).animate({ height: '+=2px' }, 100);
          });
          $(this).remove();
        });
      }
    },
    plugins: {
    }
  });

  // Default configuration
  $.bsmSelect.conf = {
    listType: 'ol',                             // Ordered list 'ol', or unordered list 'ul'

    showEffect: $.bsmSelect.effects.show,
    hideEffect: $.bsmSelect.effects.remove,
    highlightEffect: $.noop,

    addItemTarget: 'bottom',                    // Where to place new selected items in list: top or bottom
    hideWhenAdded: false,                       // Hide the option when added to the list? works only in FF
    debugMode: false,                           // Debug mode keeps original select visible

    title: 'Select...',                         // Text used for the default select label
    removeLabel: 'remove',                      // HTML used for the 'remove' link
    highlightAddedLabel: 'Added: ',             // Text that precedes highlight of added item
    highlightRemovedLabel: 'Removed: ',         // Text that precedes highlight of removed item
    extractLabel: function($o) { return $o.html(); },

    plugins: [],                                // An array of plugin objects to enable

    containerClass: 'bsmContainer',             // Class for container that wraps this widget
    selectClass: 'bsmSelect',                   // Class for the newly created <select>
    optionDisabledClass: 'bsmOptionDisabled',   // Class for items that are already selected / disabled
    listClass: 'bsmList',                       // Class for the list ($list)
    listItemClass: 'bsmListItem',               // Class for the <li> list items
    listItemLabelClass: 'bsmListItemLabel',     // Class for the label text that appears in list items
    removeClass: 'bsmListItemRemove',           // Class given to the 'remove' link
    highlightClass: 'bsmHighlight'              // Class given to the highlight <span>
  };

})(jQuery);
