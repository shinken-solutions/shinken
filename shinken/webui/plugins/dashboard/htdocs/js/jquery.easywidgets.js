/**
 * Easy Widgets 2.0 for jQuery and jQuery UI
 *
 * David Esperalta <http://www.davidesperalta.com/>
 * 
 * More information, examples and latest version in the website:
 * <http://www.bitacora.davidesperalta.com/archives/projects/easywidgets/>
 *
 * I based my work on a tutorial writen by James Padolsey
 * <http://nettuts.com/tutorials/javascript-ajax/inettuts/>
 *
 * You should have received a copy of the GNU General Public License
 * along with Easy Widgets. If not, see <http://www.gnu.org/licenses/>
 *
 */
(function($){

  ///////////////////////////
  // Public plugin methods //
  ///////////////////////////
  
  /**
   * Main public method of plugin
   *
   * Call this method to initialize the plugin, that prepare all the available
   * widgets in the document, and execute the appropiate task on every widget.
   *
   * Basically call the InitializeWidgets() private function, with the second
   * param by default: using this method we not prepare widgets on demand, but
   * prepare all widgets found in the document.
   *
   * See the mentioned function for more details, and how we use this function
   * too in another plugin public method: AddEasyWidget(), see it for details.
   *
   * @access public
   * @see InitializeWidgets()
   * @param settings Array with the plugin settings
   * @return Boolean True in every case
   *
   */
  $.fn.EasyWidgets = function(settings){
    InitializeWidgets(settings, false);
    return true;
  };

  /**
   * Add a new widget "on demand"
   *
   * This public method can be use to add a new widget "on demand" into certain
   * place. The method need the HTML markup for widget, and this can specify
   * all the available widget options.
   *
   * In this method we use the private InitializeWidgets() function, also used
   * in another public method of the plugin: EasyWidgets(). Note that in this
   * case the second param for this funtion specify that in this case we want
   * to add a widget "on demand".
   *
   * For more details see the refered private function.
   *
   * @access public
   * @see InitializeWidgets()
   * @param html String Widget HTML markup
   * @param placeId String Element ID to place the Widget
   * @param settings Array with the plugin settings
   * @return Boolean True if widget is finally added, False if not
   *
   */
  $.fn.AddEasyWidget = function(html, placeId, settings){
    var canAdd = true;
    var widget = $(html);
    var s = $.extend(true, $.fn.EasyWidgets.defaults, settings);
    if($.isFunction(s.callbacks.onAddQuery)){
      canAdd = s.callbacks.onAddQuery(widget, placeId);
    }
    if(canAdd){
      $('#'+placeId).append(html);
      if($.isFunction(s.callbacks.onAdd)){
        s.callbacks.onAdd(widget, placeId);
      }
      InitializeWidgets(s, true);
      return true;
    }else{
      return false;
    }
  };

  /**
   * Disable all widgets (fix then) in document
   *
   * This public method can be use to fix the widgets on document, in other
   * words, disable the widgets, because the user cant move this after the
   * widgets as been disables.
   * 
   * @access public
   * @see EnableEasyWidgets()
   * @param settings Array with the plugin settings
   * @return Boolean True if widgets are finally disables, False if not
   *
   */
  $.fn.DisableEasyWidgets = function(settings){
    var canDisable = true;
    var s = $.extend(true, $.fn.EasyWidgets.defaults, settings);
    if($.isFunction(s.callbacks.onDisableQuery)){
      canDisable = s.callbacks.onDisableQuery();
    }
    if(canDisable){
      $(s.selectors.places).sortable('disable');
      $(s.selectors.widget).each(function(){
        var widget = $(this);
        if(widget.hasClass(s.options.movable)){
          widget.find(s.selectors.header).css('cursor', 'default');
        }
      });
      if($.isFunction(s.callbacks.onDisable)){
        s.callbacks.onDisable();
      }
      SetCookie(s.cookies.disableName, 1, s);
      return true;
    }else{
      return false;
    }
  };

  /**
   * Enable all widgets (make movables) in document
   *
   * This public method can be use to make movables the widgets on document,
   * in other words, enable the widgets, because the user can move this after
   * the widgets as been enables.
   *
   * Note that the widgets are enables by default, so, this method have sense
   * in case that you use before another method of plugin: DisableEasyWidgets()
   *
   * @access public
   * @see DisableEasyWidgets()
   * @param settings Array with the plugin settings
   * @return Boolean True if widgets are finally enables, False if not
   *
   */
  $.fn.EnableEasyWidgets = function(settings){
    var canEnable = true;
    var s = $.extend(true, $.fn.EasyWidgets.defaults, settings);
    if($.isFunction(s.callbacks.onEnableQuery)){
      canEnable = s.callbacks.onEnableQuery();
    }
    if(canEnable){
      $(s.selectors.places).sortable('enable');
      $(s.selectors.widget).each(function(){
        var widget = $(this);
        if(widget.hasClass(s.options.movable)){
          widget.find(s.selectors.header).css('cursor', 'move');
        }
      });
      if($.isFunction(s.callbacks.onEnable)){
        s.callbacks.onEnable();
      }
      if(s.behaviour.useCookies){
        SetCookie(s.cookies.disableName, 0, s);
      }
      return true;
    }else{
      return false;
    }
  };

  /**
   * Hide all widgets in document
   *
   * This public method can be use to hide all the document visible widgets.
   * Note that this method and related is thinking if you use the plugin
   * cookies feature.
   *
   * In other case, you can use directly something like this:
   *
   * $('widgets-class-selector').hide();
   *
   * So, this method can sense if you use the plugin cookies feature, because
   * the plugin update the appropiate cookie with the needed information, to
   * mantain the widgets hidden even if user refresh the page.
   *
   * @access public
   * @see HideEasyWidget()
   * @see ShowEasyWidgets()
   * @param settings Array with the plugin settings
   * @return Boolean True in every case
   *
   */
  $.fn.HideEasyWidgets = function(settings){
    var s = $.extend(true, $.fn.EasyWidgets.defaults, settings);
    $(s.selectors.widget+':visible').each(function(){
      var canHide = true;
      var thisWidget = $(this);
      var thisWidgetId = thisWidget.attr('id');
      if($.isFunction(s.callbacks.onHideQuery)){
        canHide = s.callbacks.onHideQuery(thisWidget);
      }
      if(canHide){
        ApplyEffect(
          thisWidget,
          s.effects.widgetHide,
          s.effects.effectDuration,
          false
        );
        if(s.behaviour.useCookies && thisWidgetId){
          UpdateCookie(thisWidgetId, s.cookies.closeName, s);
        }
        if($.isFunction(s.callbacks.onHide)){
          s.callbacks.onHide(thisWidget);
        }
      }
    });
    return true;
  };

  /**
   * Show all widgets in document
   *
   * This public method can be use to show all the document hidden widgets.
   * Note that this method and related is thinking if you use the plugin
   * cookies feature.
   *
   * In other case, you can use directly something like this:
   *
   * $('widgets-class-selector').show();
   *
   * So, this method can sense if you use the plugin cookies feature, because
   * the plugin update the appropiate cookie with the needed information, to
   * mantain the widgets showing even if user refresh the page.
   *
   * @access public
   * @see ShowEasyWidget()
   * @see HideEasyWidgets()
   * @param settings Array with the plugin settings
   * @return Boolean True in every case
   *
   */
  $.fn.ShowEasyWidgets = function(settings){
    var s = $.extend(true, $.fn.EasyWidgets.defaults, settings);
    $(s.selectors.widget+':hidden').each(function(){
      var canShow = true;
      var widget = $(this);
      var widgetId = widget.attr('id');
      var haveId = ($.trim(widgetId) != '');
      if($.isFunction(s.callbacks.onShowQuery)){
        canShow = s.callbacks.onShowQuery(widget);
      }
      if(canShow){
        ApplyEffect(
          widget,
          s.effects.widgetShow,
          s.effects.effectDuration,
          true
        );
        if(haveId && s.behaviour.useCookies){
          CleanCookie(widgetId, s.cookies.closeName, s);
        }
        if($.isFunction(s.callbacks.onShow)){
          s.callbacks.onShow(widget);
        }
      }
    });
    return true;
  };

  /**
   * Show an individual widget
   *
   * This public method can be use to show an individual hidden widget.
   * Note that this method and related is thinking if you use the plugin
   * cookies feature.
   *
   * In other case, you can use directly something like this:
   *
   * $('widget-id-selector').show();
   *
   * So, this method can sense if you use the plugin cookies feature, because
   * the plugin update the appropiate cookie with the needed information, to
   * mantain the widgets showing even if user refresh the page.
   *
   * @access public
   * @see HideEasyWidget()
   * @see ShowEasyWidgets()
   * @param widgetId String Widget element identifier
   * @param settings Array with the plugin settings
   * @return Boolean True if widget finally is show, False if not
   *
   */
  $.fn.ShowEasyWidget = function(widgetId, settings){
    var canShow = true;
    var widget = $('#'+widgetId);
    if(widget.css('display') == 'none'){
      var s = $.extend(true, $.fn.EasyWidgets.defaults, settings);
      if($.isFunction(s.callbacks.onShowQuery)){
        canShow = s.callbacks.onShowQuery(widget);
      }
      if(canShow){
        ApplyEffect(
          widget,
          s.effects.widgetShow,
          s.effects.effectDuration,
          true
        );
        if(s.behaviour.useCookies){
          CleanCookie(widgetId, s.cookies.closeName, s);
        }
        if($.isFunction(s.callbacks.onShow)){
          s.callbacks.onShow(widget);
        }
        return true;
      }else{
        return false;
      }
    }else{
      return false;
    }
  };

  /**
   * Hide an individual widget
   *
   * This public method can be use to hide an individual visible widget.
   * Note that this method and related is thinking if you use the plugin
   * cookies feature.
   *
   * In other case, you can use directly something like this:
   *
   * $('widget-id-selector').hide();
   *
   * So, this method can sense if you use the plugin cookies feature, because
   * the plugin update the appropiate cookie with the needed information, to
   * mantain the widgets showing even if user refresh the page.
   *
   * @access public
   * @see ShowEasyWidget()
   * @see HideEasyWidgets()
   * @param widgetId String Widget element identifier
   * @param settings Array with the plugin settings
   * @return Boolean True if widget finally is hide, False if not
   *
   */
  $.fn.HideEasyWidget = function(widgetId, settings){
    var canHide = true;
    var widget = $('#'+widgetId);
    if(widget.css('display') != 'none'){
      var s = $.extend(true, $.fn.EasyWidgets.defaults, settings);
      if($.isFunction(s.callbacks.onHideQuery)){
        canHide = s.callbacks.onHideQuery(widget);
      }
      if(canHide){
        ApplyEffect(
          widget,
          s.effects.widgetHide,
          s.effects.effectDuration,
          false
        );
        if(s.behaviour.useCookies){
          UpdateCookie(widgetId, s.cookies.closeName, s);
        }
        if($.isFunction(s.callbacks.onHide)){
          s.callbacks.onHide(widget);
        }
        return true;
      }else{
        return false;
      }
    }else{
      return false;
    }
  };

  /////////////////////////////
  // Plugin default settings //
  /////////////////////////////

  /**
   * Plugin default settings
   *
   * This is the settings that plugin use in case that you not provide your
   * own plugin settings. Also, you dont need to provide all the settings, but
   * change only that you need: the plugin use the default settings that you
   * not provided, and also the settings that you provide.
   *
   * In other words, the plugin merge your own settings with plugin defaults.
   * 
   */
  $.fn.EasyWidgets.defaults = {

    // Behaviour of the plugin
    behaviour : {

      // Miliseconds delay between mousedown and drag start
      dragDelay : 100,

      // Miliseconds delay between mouseup and drag stop
      dragRevert : 100,

      // Determinme the opacity of Widget when start drag
      dragOpacity : 0.8,

      // Cookies (require Cookie plugin) to store positions and states
      useCookies : false
    },

    // Some effects that can be apply sometimes
    effects : {

      // Miliseconds for effects duration
      effectDuration : 500,

      // Can be none, slide or fade
      widgetShow : 'none',
      widgetHide : 'none',
      widgetClose : 'none',
      widgetExtend : 'none',
      widgetCollapse : 'none',
      widgetOpenEdit : 'none',
      widgetCloseEdit : 'none',
      widgetCancelEdit : 'none'
    },

    // Only for the optional cookie feature
    cookies : {

      // Cookie path
      path : '',

      // Cookie domain
      domain : '',

      // Cookie expiration time in days
      expires : 90,

      // Store a secure cookie?
      secure : false,

      // Cookie name for close Widgets
      closeName : 'ew-close',

      // Cookie name for disable all Widgets
      disableName : 'ew-disable',

      // Cookie name for positined Widgets
      positionName : 'ew-position',

      // Cookie name for collapsed Widgets
      collapseName : 'ew-collapse'
    },

    // Options name to use in the HTML markup
    options : {

      // To recognize a movable Widget
      movable : 'movable',

      // To recognize a editable Widget
      editable : 'editable',

      // To recognize a collapse Widget
      collapse : 'collapse',

      // To recognize a removable Widget
      removable : 'removable',

      // To recognize a collapsable Widget
      collapsable : 'collapsable',

      // To recognize Widget that require confirmation when remove
      closeConfirm : 'closeconfirm'
    },

    // Callbacks functions
    callbacks : {

      // When a Widget is added on demand, send the widget object and place ID
      onAdd : null,

      // When a editbox is closed, send the link and the widget objects
      onEdit : null,

      // When a Widget is show, send the widget object
      onShow : null,

      // When a Widget is hide, send the widget object
      onHide : null,

      // When a Widget is closed, send the link and the widget objects
      onClose : null,

      // When Widgets are enabled using the appropiate public method
      onEnable : null,

      // When a Widget is extend, send the link and the widget objects
      onExtend : null,

      // When Widgets are disabled using the appropiate public method
      onDisable : null,

      // When a editbox is closed, send a ui object, see jQuery::sortable()
      onDragStop : null,

      // When a Widget is collapse, send the link and the widget objects
      onCollapse : null,

      // When a Widget is try to added, send the widget object and place ID
      onAddQuery : null,

      // When a editbox is try to close, send the link and the widget objects
      onEditQuery : null,

      // When a Widget is try to show, send the widget object
      onShowQuery : null,

      // When a Widget is try to hide, send the widget object
      onHideQuery : null,

      // When a Widget is try to close, send the link and the widget objects
      onCloseQuery : null,

      // When a editbox is cancel (close), send the link and the widget objects
      onCancelEdit : null,

      // When Widgets are enabled using the appropiate public method
      onEnableQuery : null,

      // When a Widget is try to expand, send the link and the widget objects
      onExtendQuery : null,

      // When Widgets are disabled using the appropiate public method
      onDisableQuery : null,

      // When a Widget is try to expand, send the link and the widget objects
      onCollapseQuery : null,

      // When a editbox is try to cancel, send the link and the widget objects
      onCancelEditQuery : null,

      // When one Widget is repositioned, send the positions serialization
      onChangePositions : null,

      // When Widgets need repositioned, get the serialization positions
      onRefreshPositions : null
    },

    // Selectors in HTML markup. All can be change by you, but not all is
    // used in the HTML markup. For example, the "editLink" or "closeLink"
    // is prepared by the plugin for every Widget.
    selectors : {

      // Container of a Widget (into another element that use as place)
      // The container can be "div" or "li", for example. In the first case
      // use another "div" as place, and a "ul" in the case of "li".
      container : 'div',

      // Class identifier for a Widget
      widget : '.widget',

      // Class identifier for a Widget place (parents of Widgets)
      places : '.widget-place',

      // Class identifier for a Widget header (handle)
      header : '.widget-header',

      // Class for the Widget header menu
      widgetMenu : '.widget-menu',

      // Class identifier for Widget editboxes
      editbox : '.widget-editbox',

      // Class identifier for Widget content
      content : '.widget-content',

      // Class identifier for editbox close link or button, for example
      closeEdit : '.widget-close-editbox',

      // Class identifier for a Widget edit link
      editLink : '.widget-editlink',

      // Class identifier for a Widget close link
      closeLink : '.widget-closelink',

      // Class identifier for Widgets placehoders
      placeHolder : 'widget-placeholder',

      // Class identifier for a Widget collapse link
      collapseLink : '.widget-collapselink'
    },

    // To be translate the plugin into another languages
    // But this variables can be used to show images instead
    // links text, if you preffer. In this case set the HTML
    // of the IMG elements.
    i18n : {

      // Widget edit link text
      editText : 'Edit',

      // Widget close link text
      closeText : 'Close',

      // Widget extend link text
      extendText : 'Extend',

      // Widget collapse link text
      collapseText : 'Collapse',

      // Widget cancel edit link text
      cancelEditText : 'Cancel',

      // Widget edition link title
      editTitle : 'Edit this widget',

      // Widget close link title
      closeTitle : 'Close this widget',

      // Widget confirmation dialog message
      confirmMsg : 'Remove this widget?',

      // Widget cancel edit link title
      cancelEditTitle : 'Cancel edition',

      // Widget extend link title
      extendTitle : 'Extend this widget',

      // Widget collapse link title
      collapseTitle : 'Collapse this widget'
    }
  };

  //////////////////////////////
  // Private plugin functions //
  //////////////////////////////
  
  /**
   * Initialize the widgets
   *
   * This private function is used in two methods of the plugin, the main
   * public method: EasyWidgets() and AddEasyWidget() public method. In other
   * words, this function is the main function of the plugin, and is use to
   * initialize the widgets at a first time, and initialize the widgets added
   * on demand.
   *
   * This function separate different things into other private functions:
   * for more details see the related and used here plugin private functions.
   *
   * @access private
   * @param settings Array with the plugin settings
   * @param widgetOnDemand Boolean Widget added on demand or not
   * @return Boolean True in every case
   *
   */
  function InitializeWidgets(
   settings, widgetOnDemand){
     var b = widgetOnDemand;
     var d = $.fn.EasyWidgets.defaults;
     var s = $.extend(true, d, settings);
     $(s.selectors.widget).each(function(){
       PrepareWidgetBehaviour($(this),b,s);
     });
     RepositionedWidgets(s);
     MakeWidgetsSortables(s);
     CleanWidgetsCookies(s,b);
     return true;
  }

  /**
   * Prepare the widgets behaviour
   *
   * This private function is called from another: InitializeWidgets()
   * to prepare the behaviour of a found widget: append the widget menu
   * if is needed, put into this the appropiate links, etc.
   *
   * As you can see, another private plugin functions are used here,
   * we refer you to this functions for more details about this task.
   * However, here is an important question about this function logical:
   *
   * This function can be use to deal with "normal" widgets and widgets
   * added on demand. This function can be called to prepare certain
   * widget that as been prepared when page onload: so, this widgets
   * cannot be prepared again.
   *
   * To evit the duplication of the widget menus, basically, we find
   * for this widget menu, and, if is empty, this widget need to be
   * prepared, but, if this widget have a menu yet, cannot need to
   * be prepared.
   *
   * This condition only have sense when added widgets on demand, if
   * not is the case, no one widget have a menu before prepared, so,
   * are prepared here the first time that this function is called.
   *
   * @access private
   * @see InitializeWidgets()
   * @see AddWidgetEditLink()
   * @see AddWidgetRemoveLink()
   * @see AddWidgetCollapseLink()
   * @param widget jQuery object with a widget
   * @param widgetOnDemand Boolean Widget added on demand or not
   * @param settings Array with the plugin settings
   * @return Boolean True if widget are prepared, False if is yet prepared
   *
   */
  function PrepareWidgetBehaviour(widget, widgetOnDemand, settings){
    var s = settings;
    var widgetMenu = widget.find(s.selectors.widgetMenu);
    if(widgetMenu.html() == null){
      var widgetId = widget.attr('id');
      var haveId = ($.trim(widgetId) != '');
      widget.find(s.selectors.editbox).hide();
      if(widgetOnDemand && haveId && s.behaviour.useCookies){
        // Force this widget out of closed widgets cookie
        // because in other case is possible that widget
        // are added, but in fact not show in the document
        CleanCookie(widgetId, s.cookies.closeName, s);
      }
      if(!widgetOnDemand && haveId && s.behaviour.useCookies
       && GetCookie(s.cookies.closeName) != null){
         var cookieValue = GetCookie(s.cookies.closeName);
         if(cookieValue.indexOf(widgetId) != -1){
           // But in case of not on demand widget, is possible
           // to hide the widget, if is present in the appropiate
           // related cookie
           widget.hide();
         }
      }
      var menuWrap = '<span class="' + s.selectors
       .widgetMenu.replace(/\./, '') + '"></span>';
      widget.find(s.selectors.header).append(menuWrap);
      // Now this menu is a valid wrap to add the links
      widgetMenu = widget.find(s.selectors.widgetMenu);
      // The order of this function call is important
      // because determine the order of links appear
      AddWidgetCollapseLink(widget, widgetMenu, s);
      AddWidgetEditLink(widget, widgetMenu, s);
      AddWidgetRemoveLink(widget, widgetMenu, s);
      return true;
    }else{
      return false;
    }
  }

  /**
   * Repositioned the widgets
   *
   * This private function is called from InitializeWidgets() and is used
   * to repositioned the widgets in the appropiate places into the document.
   *
   * Some important question about this function is that the plugin can
   * repositioned the widgets follow certain string, that containt the
   * needed information.
   *
   * This string is produced in WidgetsPositionsChange() private function,
   * and bassically contain the places IDs and the widgets IDs saved in
   * a know format, that here we read to apply just later.
   *
   * Take a look at this: the mentioned string is saved in a cookie if you
   * use the cookies feature of the plugin. But in any case the plugin send
   * to you this string in the "onChangePositions()" callback.
   *
   * What is this? Suppose that you cannot use cookies, but still want to
   * repositioned the widgets. So, you can get the refered string and save
   * it in a database, for example.
   *
   * Then, just when this function is executed, you can provide this string
   * returning it in the "onRefreshPositions()" plugin callback. Then, if you
   * provide here a string that contain the widgets positions, the plugin use
   * this string to repositioned the widgets.
   *
   * If you use the cookies plugin feature, the widget read the appropiate
   * cookie, get the string previously saved (see WidgetsPositionsChange())
   * and repositioned the widgets. Of course, if you not provide any string
   * and also not use the cookies feature, the widgets cannot be positioned.
   *
   * Another thing more. You can see at WidgetsPositionsChange() how we
   * conform the appropiate string, so, in this function we read the string
   * based on the appropiate format. This string is like this:
   *
   * place-1=widget-1,widget-2|place-1=widget-3,widget-4
   *
   * Note one more thing: the order of the string is not casual: reflect the
   * real order of the places and widgets in the document when the string is
   * formed, so, the order of the widgets after this function is executed is
   * the correct, because we follow the string as is.
   *
   * @access private
   * @see InitializeWidgets()
   * @see PrepareSortablePlaces()
   * @see WidgetsPositionsChange()
   * @return Boolean True in every case
   * 
   */
  function RepositionedWidgets(settings){
    var s = settings;
    var positions = '';
    if($.isFunction(s.callbacks.onRefreshPositions)){
      positions = s.callbacks.onRefreshPositions();
    }
    // Only if not provide a string widget positions,
    // use cookies and the appropiate cookie is not empty
    if(($.trim(positions) == '') && s.behaviour.useCookies
     && GetCookie(s.cookies.positionName) != null){
       // We get the widgets positions from the cookie
       positions = GetCookie(s.cookies.positionName)
    }
    if($.trim(positions) != ''){
      // Get the widgets places IDs and widgets IDs
      var places = positions.split('|');
      var totalPlaces = places.length;
      for(var i = 0; i < totalPlaces; i++){
        // Every part contain a place ID and possible widgets IDs
        var place = places[i].split('=');
        // Validate (more or less) the format of the part that must
        // contain two element: A place ID and one or more widgets IDs
        if(place.length == 2){
          // Subpart one: the place ID
          var placeSel = '#'+place[0];
          // Subpart two: one or more widgets IDs
          var widgets = place[1].split(',');
          var totalWidgets = widgets.length;
          // Here we have a place and one or more widgets IDs
          for(var j = 0; j < totalWidgets; j++){
            if($.trim(widgets[j]) != ''){
              // So, append every widget in the appropiate place
              var widgetSel = '#'+widgets[j];
              $(widgetSel).appendTo(placeSel);
            }
          }
        }
      }
    }
    return true;
  }

  /**
   * Make widgets sortables
   *
   * This private function make found widgets as sortable items. This
   * is called from another plugin private funtion: InitializeWidgets()
   *
   * As you can see, another private plugin functions are used here:
   * we refer you to this functions for more details about this task.
   *
   * @access private
   * @see InitializeWidgets()
   * @see GetSortableItems()
   * @see PrepareSortableHeaders()
   * @see PrepareSortablePlaces()
   * @param settings Array with the plugin settings
   * @return Boolean True in every case
   * 
   */
  function MakeWidgetsSortables(settings){
    var sortables = GetSortableItems(settings);
    PrepareSortableHeaders(sortables, settings);
    PrepareSortablePlaces(sortables, settings);
    return true;
  }

  /**
   * Find widgets and places as sortables items
   *
   * And return it. This function is called from MakeWidgetsSortables()
   * to find the widgets and places as sortable items to work with this.
   *
   * @access private
   * @see MakeWidgetsSortables()
   * @param settings Array with the plugin settings
   * @return Boolean True in every case
   *
   */
  function GetSortableItems(settings){
    var fixesSel = '';
    var s = settings;
    // Iterate all the widgets in document
    $(s.selectors.widget).each(function(count){
      // When found a not movable widget
      if(!$(this).hasClass(s.options.movable)){
        // Try to get the widget ID
        if(!this.id){
          // And if not found prepare a special one
          this.id = 'fixed-widget-id-' + count;
        }
        // Because this widget (fixed) not can be
        // put as a sortable item, so, add to the
        // fixed widgets selector, to use bellow
        if(fixesSel == ''){
          fixesSel += '#'+this.id;
        }else{
          fixesSel += ',' + '#'+this.id;
        }
      }
    });
    // We prepare now the widget that cannot be put as
    // sortable items, because are fixed widgets. We cannot
    // use directly the fixed widgets selectors, because is
    // no one fixed widget is found the selector is like this:
    // :not(), that is, a emtpy "not selector", and this cause
    // problems with jQuery version 1.3
    var notFixes = '';
    if($.trim(fixesSel) == ''){
      // So, if no fixed widgets are found, dont use the not selector
      notFixes = '> '+s.selectors.container;
    }else{
      // Use only in case that one or more fixed widgets are found
      notFixes = '> '+s.selectors.container+':not(' + fixesSel + ')';
    }
    // Its all. Return not fixed widgets and places as sortable items
    return $(notFixes, s.selectors.places);
  }

  /**
   * Prepare sortables widgets headers
   *
   * This private function is called from another: MakeWidgetsSortables()
   * and is used to prepare the widget headers as sortable items. Some
   * behaviour is needed here, and the mayor part is based in the sortable
   * feature of the jQuery UI library.
   *
   * In other words, this function prepare the widgets sortable headers
   * to can be use as the widget handle, that the users can be use to move
   * the widget into one place to another.
   *
   * For more information we refer you to the jQuery UI sortable feature
   * documentation at this website for example: <http://www.api.jquery.com/>
   *
   * @access private
   * @see MakeWidgetsSortables()
   * @param sortableItems jQuery object with found sortable items
   * @param settings Array with the plugin settings
   * @return Boolean True in every case
   *
   */
  function PrepareSortableHeaders(sortableItems, settings){
    var s = settings;
    sortableItems.find(s.selectors.header).css({
      cursor: 'move'
    }).mousedown(function(e){
      var header = $(this);
      var widget = header.parent();
      sortableItems.css({width:''});
      widget.css({
        width: widget.width() + 'px'
      });
    }).mouseup(function(){
      var header = $(this);
      var widget = header.parent();
      if(!widget.hasClass('dragging')){
        widget.css({width:''});
      }else{
        $(s.selectors.places).sortable('disable');
      }
    });
    return true;
  }

  /**
   * Prepare sortables widgets places
   *
   * This private function is called from another: MakeWidgetsSortables()
   * and is used to prepare the widget places as sortable items. Some
   * behaviour is needed here, and the mayor part is based in the sortable
   * feature of the jQuery UI library.
   *
   * For more information we refer you to the jQuery UI sortable feature
   * documentation at this website for example: <http://www.api.jquery.com/>
   *
   * @access private
   * @see MakeWidgetsSortables()
   * @see WidgetsPositionsChange()
   * @param sortableItems jQuery object with found sortable items
   * @param settings Array with the plugin settings
   * @return Boolean True in every case
   *
   */
  function PrepareSortablePlaces(sortableItems, settings){
    var s = settings;
    $(s.selectors.places).sortable('destroy');
    $(s.selectors.places).sortable({
      items: sortableItems,
      containment: 'document',
      forcePlaceholderSize: true,
      handle: s.selectors.header,
      delay: s.behaviour.dragDelay,
      revert: s.behaviour.dragRevert,
      opacity: s.behaviour.dragOpacity,
      connectWith: $(s.selectors.places),
      placeholder: s.selectors.placeHolder,
      start : function(e, ui){
        $(ui.helper).addClass('dragging');
        return true;
      },
      stop : function(e, ui){
        WidgetsPositionsChange(s);
        $(ui.item).css({width : ''});
        $(ui.item).removeClass('dragging');
        $(s.selectors.places).sortable('enable');
        if($.isFunction(s.callbacks.onDragStop)){
          s.callbacks.onDragStop(e, ui);
        }
        return true;
      }
    });
    // Ok, we take this place to disable widgets based on certain cookie
    if(s.behaviour.useCookies && (GetCookie(s.cookies.disableName) == 1)){
      $.fn.DisableEasyWidgets(s);
    }
    return true;
  }

  /**
   * Handle the widgets positions changes
   *
   * This function is called from the "stop" event of sortable widgets as
   * you can see here: PrepareSortablePlaces(), and is used to provide to
   * you of a string that contain the widgets positions in certain format.
   *
   * This string structure is like:
   *
   * place-1=widget-1,widget-2|place-1=widget-3,widget-4
   *
   * See bellow how we conform this. You can save this string in a database
   * for example, and provide latter, when the "onRefreshPositions()" callback
   * is executed. So, the plugin use this string to repositioned the widgets
   * as you can see in RepositionedWidgets() function.
   *
   * @access private
   * @see RepositionedWidgets()
   * @see PrepareSortablePlaces()
   * @param settings Array with the plugin settings
   * @return Boolean True in every case
   *
   */
  function WidgetsPositionsChange(settings){
    var s = settings;
    var positions = '';
    $(s.selectors.places).each(function(){
      var widgets = '';
      var place = $(this);
      var places = place.attr('id') + '=';
      place.children(s.selectors.widget).each(function(){
        var widget = this;
        var widgetId = widget.id;
        var haveId = ($.trim(widgetId) != '');
        if(haveId){
          if(widgets == ''){
            widgets += widgetId;
          }else{
            widgets += ',' + widgetId;
          }
        }
      });
      places += widgets;
      if(positions == ''){
        positions += places;
      }else{
        positions += '|' + places;
      }
    });
    // You can save the positions string in a database, for example,
    // using the "onChangePositions()" plugin callback. So, when the
    // "onRefreshPositions()" callback is executed, you can retrieve
    // the string and returnt it: so the plugin use this string to
    // repositioned the widgets.
    if($.isFunction(s.callbacks.onChangePositions)){
      s.callbacks.onChangePositions(positions);
    }
    // @todo Maybe we only put the positions on the cookie
    // if the user font use the "onChangePositions()" callback, because
    // at this time, ever if no use the cookie value (the user provide)
    // the positions from "onRefreshPositions()" callback) the positions
    // are saved in the cookie...
    if(s.behaviour.useCookies){
      // However, you need to use the cookies feature
      // to make possible the widgets repositioned
      if(GetCookie(s.cookies.positionName) != positions){
        SetCookie(s.cookies.positionName, positions, s);
      }
    }
    return true;
  }

  /**
   * Prepare a widget collapse menu link
   *
   * @access private
   * @see PrepareWidgetBehaviour()
   * @param widget jQuery object with a widget encapsulation
   * @param widgetMenu jQuery object with a widget menu encapsulation
   * @param settings Array with the plugin settings
   * @return Boolean Truein every case
   *
   */
  function AddWidgetCollapseLink(widget, widgetMenu, settings){
    var s = settings;
    var link = '';
    var widgetId = widget.attr('id');
    var haveId = $.trim(widgetId) != '';
    var content = widget.find(s.selectors.content);
    if(widget.hasClass(s.options.collapsable)){
      if(widget.hasClass(s.options.collapse)){
        link = MenuLink(
          s.i18n.extendText,
          s.i18n.extendTitle,
          s.selectors.collapseLink
        );
        content.hide();
      }else{
        link = MenuLink(
          s.i18n.collapseText,
          s.i18n.collapseTitle,
          s.selectors.collapseLink
        );
      }
      if(haveId && s.behaviour.useCookies &&
       GetCookie(s.cookies.collapseName) != null){
         var cookieValue = GetCookie(s.cookies.collapseName);
         if(cookieValue.indexOf(widgetId) != -1){
           link = MenuLink(
             s.i18n.extendText,
             s.i18n.extendTitle,
             s.selectors.collapseLink
           );
           content.hide();
         }
      }
      $(link).mousedown(function(e){
        e.stopPropagation();
      }).click(function(){
        var canExtend = true;
        var canCollapse = true;
        var link = $(this);
        var widget = link.parents(s.selectors.widget);
        var widgetId = widget.attr('id');
        var haveId = $.trim(widgetId) != '';
        var content = widget.find(s.selectors.content);
        var contentVisible = content.css('display') != 'none';
        link.blur();
        if(contentVisible){
          if($.isFunction(s.callbacks.onCollapseQuery)){
            canCollapse = s.callbacks.onCollapseQuery(link,widget);
          }
          if(canCollapse){
            ApplyEffect(
              content,
              s.effects.widgetCollapse,
              s.effects.effectDuration,
              false
            );
            link.html(s.i18n.extendText);
            link.attr('title', s.i18n.extendTitle);
            if(s.behaviour.useCookies && widgetId){
              UpdateCookie(widgetId, s.cookies.collapseName, s);
            }
            if($.isFunction(s.callbacks.onCollapse)){
              s.callbacks.onCollapse(link, widget);
            }
          }
        }else{
          if($.isFunction(s.callbacks.onExtendQuery)){
            canExtend = s.callbacks.onExtendQuery(link, widget);
          }
          if(canExtend){
            link.html(s.i18n.collapseText);
            link.attr('title', s.i18n.collapseTitle);
            ApplyEffect(
              content,
              s.effects.widgetExtend,
              s.effects.effectDuration,
              true
            );
            if(haveId && s.behaviour.useCookies){
              CleanCookie(widgetId, s.cookies.collapseName, s);
            }
            if($.isFunction(s.callbacks.onExtend)){
              s.callbacks.onExtend(link, widget);
            }
          }
        }
        return false;
      }).appendTo(widgetMenu);
    }
    return true;
  }

  /**
   * Prepare a widget edit menu link
   *
   * @access private
   * @see PrepareWidgetBehaviour()
   * @param widget jQuery object with a widget encapsulation
   * @param widgetMenu jQuery object with a widget menu encapsulation
   * @param settings Array with the plugin settings
   * @return Boolean Truein every case
   *
   */
  function AddWidgetEditLink(widget, widgetMenu, settings){
    var s = settings;
    var link = '';
    if(widget.hasClass(s.options.editable)){
      link = MenuLink(
        s.i18n.editText,
        s.i18n.editTitle,
        s.selectors.editLink
      );
      widget.find(s.selectors.closeEdit).click(function(e){
        var link = $(this);
        var widget = link.parents(s.selectors.widget);
        var editbox = widget.find(s.selectors.editbox);
        var editLink = widget.find(s.selectors.editLink);
        link.blur();
        ApplyEffect(
          editbox,
          s.effects.widgetCloseEdit,
          s.effects.effectDuration,
          false
        );
        editLink.html(s.i18n.editText);
        editLink.attr('title', s.i18n.editTitle);
        return false;
      });
      $(link).mousedown(function(e){
        e.stopPropagation();
      }).click(function(){
        var link = $(this);
        var canShow = canHide = true;
        var widget = link.parents(s.selectors.widget);
        var editbox = widget.find(s.selectors.editbox);
        var editboxVisible = editbox.css('display') != 'none';
        link.blur();
        if(editboxVisible){
          if($.isFunction(s.callbacks.onCancelEditQuery)){
            canHide = s.callbacks.onCancelEditQuery(link, widget);
          }
          if(canHide){
            ApplyEffect(
              editbox,
              s.effects.widgetCancelEdit,
              s.effects.effectDuration,
              false
            );
            link.html(s.i18n.editText);
            link.attr('title', s.i18n.editTitle);
            if($.isFunction(s.callbacks.onCancelEdit)){
              s.callbacks.onCancelEdit(link, widget);
            }
          }
        }else{
          if($.isFunction(s.callbacks.onEditQuery)){
            canShow = s.callbacks.onEditQuery(link, widget);
          }
          if(canShow){
            link.html(s.i18n.cancelEditText);
            link.attr('title', s.i18n.cancelEditTitle);
            ApplyEffect(
              editbox,
              s.effects.widgetOpenEdit,
              s.effects.effectDuration,
              true
            );
            if($.isFunction(s.callbacks.onEdit)){
              s.callbacks.onEdit(link, widget);
            }
          }
        }
        return false;
      }).appendTo(widgetMenu);
    }
    return true;
  }
  
  /**
   * Prepare a widget remove menu link
   *
   * @access private
   * @see PrepareWidgetBehaviour()
   * @param widget jQuery object with a widget encapsulation
   * @param widgetMenu jQuery object with a widget menu encapsulation
   * @param settings Array with the plugin settings
   * @return Boolean Truein every case
   *
   */
  function AddWidgetRemoveLink(widget, widgetMenu, settings){
    var s = settings;
    var link = '';
    if(widget.hasClass(s.options.removable)){
      link = MenuLink(
        s.i18n.closeText,
        s.i18n.closeTitle,
        s.selectors.closeLink
      );
      $(link).mousedown(function(e){
        e.stopPropagation();
      }).click(function(){
        var link = $(this);
        var canRemove = true;
        var widget = link.parents(s.selectors.widget);
        var widgetId = widget.attr('id');
        var haveId = ($.trim(widgetId) != '');
        link.blur();
        if($.isFunction(s.callbacks.onCloseQuery)){
          canRemove = s.callbacks.onCloseQuery(link, widget);
        }
        if(canRemove){
          if(!widget.hasClass(s.options.closeConfirm)
            || confirm(s.i18n.confirmMsg)){
              if(haveId && s.behaviour.useCookies){
                UpdateCookie(widgetId, s.cookies.closeName, s);
              }
              ApplyEffect(
                widget,
                s.effects.widgetClose,
                s.effects.effectDuration,
                false
              );
              if($.isFunction(s.callbacks.onClose)){
                s.callbacks.onClose(link, widget);
              }
          }
        }
        return false;
      }).appendTo(widgetMenu);
    }
    return true;
  }

  /**
   * Clean widgets related cookies
   *
   * This private function is called from InitializeWidgets() and used to
   * clean certain widgets related cookies. What is this? Well, basically
   * here we find for no more used widgets IDs into the appropiate cookies
   * values, and remove from this.
   *
   * Why? Because in this form the related cookies ever still clean. ;)
   * This cookies are the "closed widgets" and "collapses widgets" cookies,
   * that store widgets IDs in the same way: separated by commas. So, find
   * widgets IDs that in fact not found in the document, and remove from the
   * appropiate cookie value, remainded the rest of the widgets IDs.
   *
   * Because this function is called from the main plugin method, called
   * itself every time that a page that contain widgets is refresh, or when
   * add widgets on demand, we only try to clean the cookies in a "random"
   * mode, because, finally, is not problem that a cookie contain widgets
   * IDs that dont exists.
   *
   * So, to save resources, we clean the cookies only in no on demand widgets,
   * and only in some "random" times, as you can see in the bellow code.
   *
   * @access private
   * @see InitializeWidgets()
   * @param settings Array with the plugin settings
   * @param widgetOnDemand Boolean Depend if deal with on demand widget or not
   * @return Boolean True in every case
   *
   */
  function CleanWidgetsCookies(settings, widgetOnDemand){
    var s = settings;
    var cleanCookies = !widgetOnDemand && s.behaviour.useCookies
      && (Math.ceil(Math.random() * 3) == 1);
    if(cleanCookies){
      var i = j = 0;
      var cookies = new Array(
        s.cookies.closeName,
        s.cookies.collapseName
      );
      var cookiesLen = cookies.length;
      var widgetsIds = new Array();
      $(s.selectors.widget).each(function(count){
        var widgetId = $(this).attr('id');
        if($.trim(widgetId) != ''){
          widgetsIds[count] = widgetId;
        }
      });
      for(i = 0; i < cookiesLen; i++){
        if(GetCookie(cookies[i])){
          var widgetId = '';
          var cleanValue = '';
          var storedValue = GetCookie(cookies[i]).split(',');
          var storedWidgets = storedValue.length;
          for(j = 0; j < storedWidgets; j++){
            widgetId = $.trim(storedValue[j]);
            if($.inArray(widgetId, widgetsIds) != -1){
              if($.trim(cleanValue) == ''){
                cleanValue += widgetId;
              }else{
                cleanValue += ','+widgetId;
              }
            }
          }
          SetCookie(cookies[i], cleanValue, s);
        }
      }
    }
    return true;
  }

  /**
   * Get a specific cookie value
   *
   * This function is based in jQuery Cookie plugin by Klaus Hartl
   *
   * @access private
   * @param name String with the cookie name
   * @return Null|String Cookie value or nothing
   *
   */
  function GetCookie(name){
    var result = null;
    if(document.cookie && $.trim(document.cookie) != ''){
      var cookies = document.cookie.split(';');
      var cookiesLen = cookies.length;
      if(cookiesLen > 0){
        for(var i = 0; i < cookiesLen; i++){
          var cookie = $.trim(cookies[i]);
          if (cookie.substring(0, name.length + 1) == (name + '=')){
            result = decodeURIComponent(cookie.substring(name.length + 1));
            break;
          }
        }
      }
    }
    return result;
  }

  /**
   * Set a specific cookie value
   *
   * This function is based in jQuery Cookie plugin by Klaus Hartl
   *
   * @access private
   * @param name String with the cookie name
   * @param value String with the cookie value
   * @param settings Array with plugin settings to use
   * @return Boolean True in every case
   *
   */
  function SetCookie(name, value, settings){
    var s = settings;
    var expires = '';
    var nType = 'number';
    if(s.cookies.expires && (typeof s.cookies.expires
     == nType) || s.cookies.expires.toUTCString){
       var date = null;
       if(typeof s.cookies.expires == nType){
         date = new Date();
         date.setTime(date.getTime() + (s.cookies.expires*24*60*60*1000));
       }else{
         date = s.cookies.expires;
       }
       // use expires attribute, max-age is not supported by IE
       expires = '; expires=' + date.toUTCString();
    }
    var path = s.cookies.path ? '; path=' + s.cookies.path : '';
    var domain = s.cookies.domain ? '; domain=' + s.cookies.domain : '';
    var secure = s.cookies.secure ? '; secure' : '';
    document.cookie = [name, '=', encodeURIComponent(value),
     expires, path, domain, secure].join('');
    return true;
  }

  /**
   * Clean a Widget Id from a cookie
   *
   * We use this in some places, so, centralize here. We clean certain
   * related cookie: two of the plugins related cookies using the same
   * structure to save their data, and can be clean in the same way.
   *
   * A string with comma separated Widgets IDs is stored in this cookies,
   * and "clean a cookie" want to say: remove certain Widget ID from this
   * cookie, because this widget is now visible or extended.
   *
   * @access private
   * @param widgetId String with a Widget identifier
   * @param cookieName String with the cookie name
   * @param settings Array with plugin settings to use
   * @return Boolean True in every case
   *
   */
  function CleanCookie(widgetId, cookieName, settings){
    var value = GetCookie(cookieName);
    if(value != null){
      if(value.indexOf(widgetId) != -1){
        value = value.replace(','+widgetId, '');
        value = value.replace(widgetId+',', '');
        value = value.replace(widgetId, '');
      }
      SetCookie(cookieName, value, settings);
    }
    return true;
  }

  /**
   * Update a Widget Id from a cookie
   *
   * We use this in some places, so, centralize here. We update certain
   * related cookie: two of the plugins related cookies using the same
   * structure to save their data, and can be update in the same way.
   *
   * A string with comma separated Widgets IDs is stored in this cookies,
   * and "update a cookie" want to say: put certain Widget ID in this
   * cookie, because this widget is now closed or collapsed.
   *
   * @access private
   * @param widgetId String with a Widget identifier
   * @param cookieName String with the cookie name
   * @param settings Array with plugin settings to use
   * @return Boolean True in every case
   *
   */
  function UpdateCookie(widgetId, cookieName, settings){
    var value = GetCookie(cookieName);
    if(value == null){
      value = widgetId;
    }else if(value.indexOf(widgetId) == -1){
      value = value+','+widgetId;
    }
    SetCookie(cookieName, value, settings);
    return true;
  }

  /**
   * Auxiliar function to prepare Widgets header menu links.
   *
   * @access private
   * @param text Link text
   * @param title Link title
   * @param aClass CSS class (behaviour) of link
   * @return String HTML of the link
   *
   */
  function MenuLink(text, title, aClass){
    var l = '<a href="#" title="TITLE" class="CLASS">TEXT</a>';
    l = l.replace(/TEXT/g, text);
    l = l.replace(/TITLE/g, title);
    l = l.replace(/CLASS/g, aClass.replace(/\./, ''));
    return l;
  }

  /**
   * Auxiliar function to show, hide and apply effects.
   *
   * @access private
   * @param jqObj jQuery object to apply the effect and show or hide
   * @param effect String that identifier what effect must be applied
   * @param duration Miliseconds to the effect duration
   * @param show Boolean True if want to show the object, False to be hide
   * @return Boolean True in every case
   *
   */
  function ApplyEffect(jqObj, effect, duration, show){
    var n = 'none', 
        f = 'fade',
        s = 'slide';
    if(!show){
      if(effect == n){
        jqObj.hide();
      }else if(effect == f){
        jqObj.fadeOut(duration);
      }else if(effect == s){
        jqObj.slideUp(duration);
      }
    }else{
      if(effect == n){
        jqObj.show();
      }else if(effect == f){
        jqObj.fadeIn(duration);
      }else if(effect == s){
        jqObj.slideDown(duration);
      }
    }
    return true;
  }
})(jQuery);