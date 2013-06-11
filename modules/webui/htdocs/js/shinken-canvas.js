
// some classic Canvas operations
function draw_arc(ctx, x, y, radius, startAngle, endAngle, clockwise, color, lineWidth, alpha){
    var saved_lineWidth = ctx.lineWidth;
    var saved_color = ctx.strokeStyle;
    var saved_alpha = ctx.globalAlpha;
    if(typeof alpha != 'undefined'){
	console.log('Set alpha to'+alpha);
	ctx.globalAlpha = alpha;
    }
    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    ctx.beginPath();
    ctx.arc(x, y, radius, startAngle, endAngle, clockwise);
    ctx.stroke();
    ctx.strokeStyle = saved_color;
    ctx.lineWidth = saved_lineWidth;
    ctx.globalAlpha = saved_alpha;
}


function fill_arc(ctx, x, y, radius, startAngle, endAngle, clockwise, color){
    var saved_color = ctx.fillStyle;
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x, y, radius, startAngle, endAngle, clockwise);
    ctx.fill();
    ctx.fillStyle = saved_color;
}

function draw_line(ctx, x, y, x2, y2, color, lineWidth, alpha){
    var saved_lineWidth = ctx.lineWidth;
    var saved_color = ctx.strokeStyle;
    var saved_alpha = ctx.globalAlpha;
    if(typeof alpha != 'undefined'){
        console.log('Set alpha to'+alpha);
        ctx.globalAlpha = alpha;
    }

    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    
    ctx.beginPath();
    ctx.moveTo(x,y);
    ctx.lineTo(x2, y2);
    ctx.closePath();
    ctx.stroke();
    
    ctx.strokeStyle = saved_color;
    ctx.lineWidth = saved_lineWidth;
    ctx.globalAlpha = saved_alpha;
}    




function fill_semi_elipse(ctx, cx, cy, r, color, clock){
    var saved_color = ctx.fillStyle;
    ctx.fillStyle = color;
    ratio = 4;
    cy *= ratio;
    ctx.scale(1, 1/ratio);
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI, clock);
    ctx.fill();
    ctx.fillStyle = saved_color;
    ctx.closePath();
    ctx.scale(1, ratio);
}


function draw_semi_elipse(ctx, cx, cy, r, color, clock){
    var saved_color = ctx.strokeStyle;
    ctx.strokeStyle = color;
    ctx.lineWidth = 1;
    ratio = 4;
    cy *= ratio;
    ctx.scale(1, 1/ratio);
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI, clock);
    ctx.stroke();
    ctx.strokeStyle = saved_color;
    
    ctx.closePath();
    ctx.scale(1, ratio);
}




function draw_text_along_arc(ctx, str, centerX, centerY, radius, angle_offset, font, fillStyle, strokeStyle, lineWidth){

    ctx.save();
    var angle = Math.PI * 0.25;
    
    ctx.font = font;
    ctx.fillStyle = fillStyle;
    ctx.strokeStyle = strokeStyle;
    ctx.lineWidth = lineWidth;
    
    ctx.translate(centerX, centerY);
    ctx.rotate(-1 * angle / 2);
    ctx.rotate(-1 * (angle / str.length) / 2);
    
    ctx.rotate(angle_offset);
    ctx.rotate((2*Math.PI) / 40);
    
    for (var n = 0; n < str.length; n++) {
	// We want a total round with 40chars
	ctx.rotate((2*Math.PI) / 30);
	//ctx.rotate(angle / str.length);
        ctx.save();
        ctx.translate(0, -1 * radius);
        var char = str[n];
        ctx.fillText(char, 0, 0);
        ctx.restore();
    }
    ctx.restore();
}
