



$(function(){
    var test_canvas = $('#host_canvas')[0];
    var ctx = test_canvas.getContext('2d');

    // Draw the host name
    var hname = $('#host_canvas').data('hname');
    ctx.font      = "bold 22px Verdana";
    ctx.fillStyle = "#555";
    ctx.fillText(hname, 150, 50);
    
    // Purple : '#c1bad9', '#a79fcb'
    // Green  : '#A6CE8D', '#81BA6B'
    // Blue   : '#DEF3F5', '#89C3C6'
    // Red    : '#dc4950', '#e05e65'
    // Orange : '#F1B16E', '#EC9054'
    var main_colors = {'unknown' : '#c1bad9', 'ok' : '#DEF3F5', 'warning' : '#F1B16E' , 'critical' : '#dc4950'};
    var huge_colors = {'unknown' : '#a79fcb', 'ok' : '#89C3C6', 'warning' : '#EC9054' , 'critical' : '#e05e65'};
    

    var main_color = main_colors[all_states['global']];//'#F1B16E';//'#c1bad9';
    var huge_color = huge_colors[all_states['global']];//'#EC9054'; //'#a79fcb';
    var line_color = huge_color;

    var line_s = 2;
    /*
    // Inner circle
    draw_arc(ctx, 80, 80, 32, 0, 2*Math.PI, true, main_color, 2, 0.5);
    draw_arc(ctx, 80, 80, 33, 0, 2*Math.PI, true, huge_color, 2, 0.5);
    */

    // Middle one
    draw_arc(ctx, 80, 80, 45, 0, 2*Math.PI, true, main_color, 2, 0.3);
    draw_arc(ctx, 80, 80, 46, 0, 2*Math.PI, true, main_color, 2, 0.3);
    // The left part of the middle
    draw_arc(ctx, 80, 80, 44, 0.7*Math.PI, 1.1*Math.PI, false, huge_color, 4, 0.5);
    //Top rigth art of the middle
    draw_arc(ctx, 80, 80, 44, 1.5*Math.PI, 2*Math.PI, false, huge_color, 4, 0.5);
  

    // Before last one
    // Middle one
    draw_arc(ctx, 80, 80, 60, Math.PI, 0.4*Math.PI, false, main_color, 2, 0.5);
    draw_arc(ctx, 80, 80, 61, Math.PI, 0.4*Math.PI, false, main_color, 2, 0.5);
    // The left part of the before last 
    draw_arc(ctx, 80, 80, 59, Math.PI, 1.7*Math.PI, false, huge_color, 5);
    //Top rigth art of the middle
    draw_arc(ctx, 80, 80, 59, 0, 0.4*Math.PI, false, huge_color, 5);

    // Outer one
    //draw_arc(ctx, 80, 80, 36, 0, 2*Math.PI, true, 'blue', 1);
    //draw_arc(ctx, 80, 80, 38, 0, 2*Math.PI, true, 'orange', line_s);

    /////////////// The status icon
    // Put the disks. From now only random things
    var img_status = document.createElement('img');
    var img_size = 64;
    img_status.onload=function(){
	var o = 80 - (img_size/2);
        ctx.drawImage(img_status, o, o, img_size, img_size);
    };
    img_status.src = '/static/img/icons/state_up.png';
    
    
    //////////////// Lines part
    // Now the line from the left part to down, in 3 parts
    draw_line(ctx, 20, 80, 20, 100, line_color, 1, 0.5);
    draw_line(ctx, 20, 100, 50, 140, line_color, 1, 0.5);
    draw_line(ctx, 50, 140, 50, 200, line_color, 1, 0.5);

    // Now a small step on the rigth, before disks
    draw_line(ctx, 50, 200, 70, 200, line_color, 1, 0.5);
    // And a small vertical line for disks
    draw_line(ctx, 70, 180, 70, 220, line_color, 1, 0.5);

    // Put the disks. From now only random things
    var img = document.createElement('img');
    var pos_x = 75;
    var pos_y = 170;
    img.onload=function(){
	console.log('All disks');
	console.log(all_disks);
	for(var i=0; i<all_disks.length; i++){
            ctx.drawImage(img, 0, 0, 70, 18, pos_x, pos_y, 70, 18);
	    var d_name = all_disks[i][0];
	    var d_value = all_disks[i][1]/100;
            var offset = 70*d_value;
            ctx.drawImage(img, 0, 18, offset, 18, pos_x, pos_y, offset, 18);
	    
	    // And draw the disk name
	    console.log('disk'+d_name+''+d_value);
	    ctx.font      = "bold 11px Verdana";
	    ctx.fillStyle = "#777";
	    ctx.fillText(d_name.slice(-8), pos_x + 5, pos_y + 13);

	    var span = $(document.createElement('span'));
	    span.html('');
	    span.css('width', '70px');
	    span.css('height','18px');
	    span.css('display','inline-block');
	    span.css('position', 'absolute');
	    span.css('left', pos_x+15);
	    span.css('top', pos_y+15);
	    span.css('cursor', 'pointer');
	    span.on('click', function(){
		$('#to_tab_disks').tab('show');
	    });
	    $('#host_left_bloc').append(span);

	    // Now prepare the next disk
	    pos_y += 25;
	}
    };

    img.src = '/static/images/bar_horizontal.png';
    //Now the right par ofthe disks to go to the CPU
    draw_line(ctx, 160, 200, 200, 200, line_color, 1, 0.5);
    // Now the part that is going upper to the center
    // Warning : on the same level as the left part
    draw_line(ctx, 200, 200, 250, 140, line_color, 1, 0.5);
    
    // Now a big line to the rigth
    draw_line(ctx, 250, 140, 415, 140, line_color, 1, 0.5);
    
    // A line that go to the CPU on the bottom
    draw_line(ctx, 280, 140, 330, 200, line_color, 1, 0.5);
});