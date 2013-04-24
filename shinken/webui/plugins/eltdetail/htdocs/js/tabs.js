// when we show a tab, we put the #hash on the windows address so the refresh will go here
$(window).ready(function(){
    $('.link_to_tab').on('shown', function (e) {
	console.log('Show the tab');
	// We get the hach in the href, thanks bootstrap
	var hash = $(this).attr('href');
	window.location.hash = hash;
    })
});
