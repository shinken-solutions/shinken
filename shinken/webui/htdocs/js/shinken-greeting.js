    $(document).ready( function() {
        var textArray = [
            'Hi,',
            'Hello, ',
            'Howdy, ',
            'Hallo, ',
            'Salut, ',
            'Ciao, ',
            '你好, ',
            'алло́,  ',
            'Hola, ',
            '???'  /**/
        ];
        $('#text-box').randomText( textArray, 0, "El Randomizah!" ); // ( array, interval, ["reload text or html"] )
    });
    // custom jquery plugin loadText()
    $.fn.randomText = function( textArray, interval, randomEle, prevText ) {
        var obj = $(this);
        if( $('#text-content').length == 0 ){ obj.append('<div id="text-content">'); }
        var textCont = $('#text-content');
        if( typeof randomEle != 'undefined' ){ if( $('#randomizer').length == 0 ){ obj.append('<a href="javascript:;" id="randomizer"><em>' + randomEle ); } }
        textCont.fadeOut( 'slow', function() {
            var chosenText = random_array( textArray );
            while( chosenText == prevText ) { chosenText = random_array( textArray ); }
            textCont.empty().html( chosenText );
            textCont.fadeIn( 'slow' );
            sendText = chosenText;
        });
        timeOut = setTimeout( function(){ obj.randomText( textArray, interval, randomEle, sendText ); }, interval );
        $("#randomizer").click( function(){
            if( !textCont.is(':animated') ) { clearTimeout( timeOut ); obj.randomText( textArray, interval, randomEle, sendText );} // animation check prevents "too much recursion" error in jQuery
        });
    }
    //public function
    function random_array( aArray ) {
        var rand = Math.floor( Math.random() * aArray.length + aArray.length );
        var randArray = aArray[ rand - aArray.length ];
        return randArray;
    }