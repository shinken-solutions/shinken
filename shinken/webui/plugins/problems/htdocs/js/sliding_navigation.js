$(document).ready(
    function()
    {
	slide_menu(".sliding-navigation", 25, 15);
    });

function slide_menu(navigation_id, pad_out, pad_in)
{
    // creates the target paths
    var list_elements = navigation_id + " li.sliding-element";
    var link_elements = list_elements + " a";

    // creates the hover-slide effect for all link elements
    $(link_elements).each(
	function(i)
	{
	    $(this).hover(
		function()
		{
		    $(this).animate({ paddingLeft: pad_out }, 150);
		},
		function()
		{
		    $(this).animate({ paddingLeft: pad_in }, 150);
		});
	});
}

