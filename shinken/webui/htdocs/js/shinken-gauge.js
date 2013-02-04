


if (typeof console === "undefined" || typeof console.log === "undefined") {
    console = {};
    console.log = function() {};
}

// Initialize all_donuts only if not done before
if (typeof all_donuts === "undefined"){
    all_donuts = [];
}

function DonutChart(canv_id){
    console.log('creating a donut'+canv_id);
    this.name = canv_id;
    this.canvas = document.getElementById(canv_id);
    if(!this.canvas){
	this.valid = false
	return;
    }
    this.valid = true;
    this.ctx    = this.canvas.getContext('2d')
    // Look at the center point
    this.x      = 50;
    this.y      = 55;

    // About main radius and donut size
    this.radius = 48;                    // Arc radius
    // The start and end of the donu
    this.startAngle = Math.PI/2 + Math.PI * 23 / 12;
    this.endAngle   = Math.PI/2 + Math.PI / 12;
    this.clockwise  = true;
    // The space between the 2 main arcs
    this.space_l    = 8;
    // The size of the lines
    this.line_size  = 1.5;

    // Value gradient and some colors
    this.grd = this.ctx.createRadialGradient(this.x, this.y, this.radius, this.x, this.y, this.radius - this.space_l);
    // The color depends on the state, so first get it
    this.state = $(this.canvas).data('state');
    // Uknown go in purple

    // Ok: green
    // Warning : orange
    // Critical : red
    // unknown or other : purple
    if(this.state == 'ok'){
	this.grd.addColorStop(0, '#A6CE8D');
        this.grd.addColorStop(1, '#81BA6B');
    }else if(this.state == 'warning') {
	this.grd.addColorStop(0, '#F1B16E');
        this.grd.addColorStop(1, '#EC9054');

    }else if(this.state == 'critical') {
        this.grd.addColorStop(0, '#dc4950');
        this.grd.addColorStop(1, '#e05e65');
    }else{
	this.grd.addColorStop(0, '#c1bad9');
        this.grd.addColorStop(1, '#a79fcb');
    }
    this.color_value    = this.grd;
    this.color_external = 'rgba(0,0,0,.2)';
    this.color_background = '#eeeeee';

    // Animation time in ms, here 1s
    this.animation_time = 1000;
    // And animate each 50ms
    this.interval_update = 50;


    // Now search the ending round, the more funny part indeed
    this.final_pct = $(this.canvas).data('value') / 100;
    this.pct = Math.max(0.05, 0.05);
    this.nb_steps = this.animation_time / this.interval_update;
    console.log('Will need' + this.nb_steps + 'steps');
    this.pct_step = (this.final_pct - this.pct) / this.nb_steps;
    console.log('pct_step'+this.pct_step);

}


function _draw_arc(x, y, radius, startAngle, endAngle, clockwise, color, lineWidth){
    var savec_lineWidth = this.ctx.lineWidth;
    var saved_color = this.ctx.strokeStyle;
    this.ctx.strokeStyle = color;
    this.ctx.lineWidth = lineWidth;
    this.ctx.beginPath();
    this.ctx.arc(x, y, radius, startAngle, endAngle, clockwise);
    this.ctx.stroke();
    this.ctx.strokeStyle = saved_color;
    this.ctx.lineWidth = savec_lineWidth;
}
DonutChart.prototype.draw_arc = _draw_arc;

/*
function draw_arc(ctx, x, y, radius, startAngle, endAngle, clockwise, color, lineWidth){
    var savec_lineWidth = ctx.lineWidth;
    var saved_color = ctx.strokeStyle;
    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    ctx.beginPath();
    ctx.arc(x, y, radius, startAngle, endAngle, clockwise);
    ctx.stroke();
    ctx.strokeStyle = saved_color;
    ctx.lineWidth = savec_lineWidth;
}*/

function _fill_arc(x, y, radius, startAngle, endAngle, clockwise, color){
    var saved_color = this.ctx.fillStyle;
    this.ctx.fillStyle = color;
    this.ctx.beginPath();
    this.ctx.arc(x, y, radius, startAngle, endAngle, clockwise);
    this.ctx.fill();
    this.ctx.fillStyle = saved_color;
}
DonutChart.prototype.fill_arc = _fill_arc;


function update_donuts(){
    $.each(all_donuts, function(i, donut){
	//update_donut(donut);
	donut.update();
    });
}


function update(){
    

    var pct = this.pct;
    var final_pct = this.final_pct;
    if (this.pct >= this.final_pct){
	return;
    }
    //console.log('Updating donut');
    this.pct += this.pct_step;
    
    var o = Math.max(0.04, this.pct);
    o = Math.min(0.96, o);
    o = o*2;
    //console.log('O='+o);
    // Now go from polar to cartesian
    var theta = (0.5 * Math.PI) + Math.PI*o;
    var end_x = this.x + (this.radius-(this.space_l/2)) * Math.cos(theta);
    var end_y = this.y + (this.radius-(this.space_l/2)) * Math.sin(theta);
    //console.log('END POS'+end_x+' '+end_y);

    this.fill_arc(end_x, end_y, this.space_l/2, 0, 2*Math.PI, false, this.grd);

    this.draw_arc(this.x, this.y, this.radius - (this.space_l/2), theta, this.endAngle, this.clockwise, this.grd, this.space_l);
}
DonutChart.prototype.update = update;



function get_donut(name){
    console.log('get_donut::'+name);
    donut = new DonutChart(name);
    if(!donut.valid){
	return null;
    }
    console.log("GO");
    console.log('Go canvas'+donut.canv);
    
    console.log('Init+'+donut.startAngle+' '+donut.endAngle);
    
    
    // fist the outter arc
    donut.draw_arc(donut.x, donut.y, donut.radius, donut.startAngle, donut.endAngle, donut.clockwise, donut.color_external, donut.line_size);
    
    // Then the inner one
    donut.draw_arc(donut.x, donut.y, donut.radius - donut.space_l, donut.startAngle, donut.endAngle, donut.clockwise, donut.color_external, donut.line_size);
    
    // Fill the background of the MAIN part
    donut.draw_arc(donut.x, donut.y, donut.radius - (donut.space_l/2), donut.startAngle, donut.endAngle, donut.clockwise, donut.color_background, donut.space_l);

    // Now The the left ending arc
    donut.draw_arc(40, 98, donut.space_l/2, -Math.PI/2, (3/4) * Math.PI, false, donut.color_external, donut.line_size);
    // And fill the background
    donut.fill_arc(40, 98, donut.space_l/2, -Math.PI/2, (3/4) * Math.PI, false, donut.color_background);


    // And the Right one
    donut.draw_arc(61, 98, donut.space_l/2, 0.7*(Math.PI/2), 1.00*(Math.PI+(Math.PI*1)/2), false, donut.color_external, donut.line_size);
    // Fil lthe background color into it
    donut.fill_arc(61, 98, donut.space_l/2, 0.7*(Math.PI/2), 1.00*(Math.PI+(Math.PI*1)/2), false, donut.color_background);
    

    // Now fill the starting value
    donut.fill_arc(40, 98, donut.space_l/2, 0, 2 * Math.PI, false, donut.color_value);

    // A frist update to draw the values
    donut.update();
    
    return donut;
}


function register_all_donuts(){
    $('.donut_canvas').each(function(id, elt){
	console.log('Oh a donut canvas?'+elt.id);
	d = get_donut(elt.id);
	if(d != null){
	    all_donuts.push(d);
	}
    });
}


$(function(){
    register_all_donuts();
    /*
    $('.donut_canvas').each(function(id, elt){
	console.log('Oh a donut canvas?'+elt.id);
	d = get_donut(elt.id);
	if(d != null){
	    all_donuts.push(d);
	}
    });*/
    
    setInterval("update_donuts();", 50);
    
});




// Now the cylinders


function draw_cylinder(ctx, value){
    //var canvas = document.getElementById('stage');
    //var ctx = canvas.getContext('2d');

    var value_color = '#89C3C6';
    var back_color = '#DEF3F5';

    var value_offset = 90 - Math.floor(value*0.8);

    console.log('Value offset '+value_offset);

    // Draw the side bars
    ctx.fillStyle=back_color;
    ctx.fillRect( 0/*35*/, 10/*20*/, 30, 80);
    ctx.strokeStyle = 'grey';
    ctx.strokeRect( 0, 10, 30, 80);

    // Draw the top BAR
    fill_semi_elipse(ctx, 15/*50*/, 10, 15, back_color, true);
    fill_semi_elipse(ctx, 15, 10, 15, back_color, false);

    
    // Draw the value base
    draw_semi_elipse(ctx, 15, 90, 15, value_color, false);
    draw_semi_elipse(ctx, 15, 90, 15, value_color, true);

    // Draw the lower value
    fill_semi_elipse(ctx, 15, 90, 15, value_color, false);

    // Draw corpus value
    var grd = ctx.createLinearGradient(0, 0, 0, 150);
    grd.addColorStop(0, '#8ED6FF');
    grd.addColorStop(1, '#004CB3');

    ctx.fillStyle=value_color;
    
    ctx.fillRect( 1, value_offset, 28, 90-value_offset);

    // Draw the top value
    fill_semi_elipse(ctx, 15, value_offset, 15, value_color, true);
    fill_semi_elipse(ctx, 15, value_offset, 15, value_color, false);
    draw_semi_elipse(ctx, 15, value_offset, 15, 'grey', false);
    draw_semi_elipse(ctx, 15, value_offset, 15, 'grey', true);
    
    // Draw the BAR low one
    draw_semi_elipse(ctx, 15, 90, 15, 'grey', false);

    // Draw the bar top circle
    draw_semi_elipse(ctx, 15, 10, 15, 'grey', false);
    draw_semi_elipse(ctx, 15, 10, 15, 'grey', true);
}


function register_all_cylinders(){
    $('.cylinder_canvas').each(function(id, elt){
        console.log('Oh a cylinder canvas?'+elt.id);
        //var canvas = document.getElementById('stage');
        var ctx = elt.getContext('2d');
        var value = $(elt).data('value');
        draw_cylinder(ctx, value);
    });
}

$(function(){

    /*$('.cylinder_canvas').each(function(id, elt){
	console.log('Oh a cylinder canvas?'+elt.id);
	//var canvas = document.getElementById('stage');
	var ctx = elt.getContext('2d');
	var value = $(elt).data('value');
	draw_cylinder(ctx, value);
    });*/

    register_all_cylinders();
    
});
