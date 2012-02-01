// Badger v1.0 by Daniel Raftery
// http://thrivingkings.com/badger
//
// http://twitter.com/ThrivingKings

(function( $ )
	{
	$.fn.badger = function(badge, callback) 
		{
  		var badgerExists = this.find('#Badger').html();
  		
  		// Clear the badge
  		if(!badge)
  			{
  			if(badgerExists)
  				{ this.find('#Badger').remove(); }
  			}
  		else
  			{
			// Figuring out badge data
			var oldBadge = this.find('#Badge').text();
			if(badge.charAt(0)=='+')
				{ 
				if(isNaN(badge.substr(1)))
					{ badge = oldBadge + badge.substr(1); }
				else
					{ badge = Math.round(Number(oldBadge) + Number(badge.substr(1))); }
				}
			else if(badge.charAt(0)=='-')
				{ 
				if(isNaN(badge.substr(1)))
					{ badge = oldBadge - badge.substr(1); }
				else
					{ badge = Math.round(Number(oldBadge) - Number(badge.substr(1))); }
				}
				
				
			// Don't add duplicates
			if(badgerExists)
				{ this.find('#Badge').html(badge); }
			else
				{ this.append('<div class="badger-outter" id="Badger"><div class="badger-inner"><p class="badger-badge" id="Badge">'+badge+'</p></div></div>'); }
				
			// Badger text or number class
			if(isNaN(badge))
				{ this.find('#Badge').removeClass('badger-number').addClass('badger-text'); }
			else
				{ this.find('#Badge').removeClass('badger-text').addClass('badger-number'); }
			// Send back badge
			if(callback) { callback(badge); }
			}
		};
})( jQuery );