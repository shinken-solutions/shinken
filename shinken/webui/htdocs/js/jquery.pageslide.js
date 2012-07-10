/*
 * jQuery pageSlide
 * Version 2.0
 * http://srobbin.com/jquery-pageslide/
 *
 * jQuery Javascript plugin which slides a webpage over to reveal an additional interaction pane.
 *
 * Copyright (c) 2011 Scott Robbin (srobbin.com)
 * Dual licensed under the MIT and GPL licenses.
*/

$(function(){
    // Convenience vars for accessing elements
    var $body = $('body'),
    $pageslide = $('#pageslide');
    var already_load = false;

    var _sliding = false,   // Mutex to assist closing only once
    _lastCaller;        // Used to keep track of last element to trigger pageslide

    // If the pageslide element doesn't exist, create it
    if( $pageslide.length == 0 ) {
        $pageslide = $('<div />').attr( 'id', 'pageslide' )
            .css( 'display', 'none' )
            .appendTo( $('body') );
    }

    /*
     * Private methods
     */
    function _load( url, useIframe ) {
        // Are we loading an element from the page or a URL?
        if ( url.indexOf("#") === 0 ) {
	    // We load only if we do not already did it
	    if(!already_load){
		// Load a page element
		$(url).clone(true).appendTo( $pageslide.empty() ).show();
	    }
	    already_load=true;
        } else {
            // Load a URL. Into an iframe?
            if( useIframe ) {
                var iframe = $("<iframe />").attr({
                    src: url,
                    frameborder: 0,
                    hspace: 0
                })
                    .css({
                        width: "100%",
                        height: "100%"
                    });

                $pageslide.html( iframe );
            } else {
                $pageslide.load( url );
            }

            $pageslide.data( 'localEl', false );

        }
    }

    // Function that controls opening of the pageslide
    function _start( direction, speed ) {
        var slideWidth = $pageslide.outerWidth( true ),
        bodyAnimateIn = {},
        slideAnimateIn = {};

        // If the slide is open or opening, just ignore the call
        if( $pageslide.is(':visible') || _sliding ) return;
        _sliding = true;

        switch( direction ) {
        case 'left':
            $pageslide.css({ left: 'auto', right: '-' + slideWidth + 'px' });
            bodyAnimateIn['margin-left'] = '-=' + slideWidth;
            slideAnimateIn['right'] = '+=' + slideWidth;
            break;
        default:
            $pageslide.css({ left: '-' + slideWidth + 'px', right: 'auto' });
            bodyAnimateIn['margin-left'] = '+=' + slideWidth;
            slideAnimateIn['left'] = '+=' + slideWidth;
            break;
        }

        // Animate the slide, and attach this slide's settings to the element
        $body.animate(bodyAnimateIn, speed);
        $pageslide.show()
            .animate(slideAnimateIn, speed, function() {
                _sliding = false;
            });
    }

    /*
     * Declaration
     */
    $.fn.pageslide = function(options) {
        var $elements = this;

        // On click
        $elements.click( function(e) {
            var $self = $(this),
            settings = $.extend({ href: $self.attr('href') }, options);

            // Prevent the default behavior and stop propagation
            e.preventDefault();
            e.stopPropagation();

            if ( $pageslide.is(':visible') && $self[0] == _lastCaller ) {
                // If we clicked the same element twice, toggle closed
                $.pageslide.close();
            } else {
                // Open
                $.pageslide( settings );

                // Record the last element to trigger pageslide
                _lastCaller = $self[0];
            }
        });
    };

    /*
     * Default settings
     */
    $.fn.pageslide.defaults = {
        speed:      200,        // Accepts standard jQuery effects speeds (i.e. fast, normal or milliseconds)
        direction:  'right',    // Accepts 'left' or 'right'
        modal:      false,      // If set to true, you must explicitly close pageslide using $.pageslide.close();
        iframe:     true,       // By default, linked pages are loaded into an iframe. Set this to false if you don't want an iframe.
        href:       null        // Override the source of the content. Optional in most cases, but required when opening pageslide programmatically.
    };

    /*
     * Public methods
     */

    // Open the pageslide
    $.pageslide = function( options ) {
	// Extend the settings with those the user has provided
        var settings = $.extend({}, $.fn.pageslide.defaults, options);

	// Are we trying to open in different direction?
        if( $pageslide.is(':visible') && $pageslide.data( 'direction' ) != settings.direction) {
            $.pageslide.close(function(){
                _load( settings.href, settings.iframe );
                _start( settings.direction, settings.speed );
            });
        } else {
            _load( settings.href, settings.iframe );
            if( $pageslide.is(':hidden') ) {
                _start( settings.direction, settings.speed );
            }
        }

        $pageslide.data( settings );
    }

    // Close the pageslide
    $.pageslide.close = function( callback ) {
        var $pageslide = $('#pageslide'),
        slideWidth = $pageslide.outerWidth( true ),
        speed = $pageslide.data( 'speed' ),
        bodyAnimateIn = {},
        slideAnimateIn = {}

        // If the slide isn't open, just ignore the call
        if( $pageslide.is(':hidden') || _sliding ) return;
        _sliding = true;

        switch( $pageslide.data( 'direction' ) ) {
        case 'left':
            bodyAnimateIn['margin-left'] = '+=' + slideWidth;
            slideAnimateIn['right'] = '-=' + slideWidth;
            break;
        default:
            bodyAnimateIn['margin-left'] = '-=' + slideWidth;
            slideAnimateIn['left'] = '-=' + slideWidth;
            break;
        }

        $pageslide.animate(slideAnimateIn, speed);
        $body.animate(bodyAnimateIn, speed, function() {
            $pageslide.hide();
            _sliding = false;
            if( typeof callback != 'undefined' ) callback();
        });
    }

    /* Events */

    // Don't let clicks to the pageslide close the window
    $pageslide.click(function(e) {
        e.stopPropagation();
    });

    // Close the pageslide if the document is clicked or the users presses the ESC key, unless the pageslide is modal
    $(document).bind('click keyup', function(e) {
	// If this is a keyup event, let's see if it's an ESC key
        if( e.type == "keyup" && e.keyCode != 27) return;

	// Make sure it's visible, and we're not modal
	if( $pageslide.is( ':visible' ) && !$pageslide.data( 'modal' ) ) {
	    $.pageslide.close();
	}
    });

});