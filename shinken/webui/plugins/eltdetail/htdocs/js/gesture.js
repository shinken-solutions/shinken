var oldX; var oldY;
var canvas;
var ctx;
var _r = new DollarRecognizer();
var _points = [];
var isMouseDown = false; // mouse only bool
var threshold = 3; // number of pixels required to be moved for a movement to count


$(document).ready(function(){
    canvas = document.getElementById("canvas");

    ctx = canvas.getContext("2d");


    function get_pos(e){
	// For all devices management, we should
	// compute as global pos minus the offset of the canvas
	// to getthe real pos in the canvas
	e._x = e.clientX - canvas.offsetLeft;
	e._y = e.clientY - canvas.offsetTop;
    }


    // If we are in an ipad/android thing
    canvas.addEventListener('touchstart', function(e) {

	e.preventDefault();
	_points = [];
	var touch = e.touches[0];
	get_pos(touch);
	ctx.beginPath();
	ctx.strokeStyle = "#bae1ff";
	ctx.lineCap = "round";
	ctx.lineJoin = "round";
	ctx.lineWidth = 4;
	ctx.shadowColor = 'rgba(169,236,255,0.1)';
	ctx.shadowOffsetX = 0;
	ctx.shadowOffsetY = 0;
	ctx.shadowBlur = 10;
	oldX = touch._x;//pageX;
	oldY = touch._y;//pageY;
	ctx.moveTo(touch._x,touch._y);
    }, false);

    // Or in a mouse case
    canvas.addEventListener('mousedown', function(e) {
	get_pos(e);

	isMouseDown = true;
	e.preventDefault();
	_points = [];

	ctx.beginPath();
	ctx.strokeStyle = "#bae1ff";
	ctx.lineCap = "round";
	ctx.lineJoin = "round";
	ctx.lineWidth = 4;
	ctx.shadowColor = 'rgba(169,236,255,0.1)';
	ctx.shadowOffsetX = 0;
	ctx.shadowOffsetY = 0;
	ctx.shadowBlur = 10;
        oldX = e._x;
        oldY = e._y;
	ctx.moveTo(e._x,e._y);
    }, false);


    // And then we move.
    // First ipad, then pc
    canvas.addEventListener('touchmove', function(e) {
	if (oldX - e.pageX < 3 && oldX - e.pageX > -3) {
	    return;
	}
	if (oldY - e.pageY < 3 && oldY - e.pageY > -3) {
	    return;
	}
	var touch = e.touches[0];
	get_pos(touch);
	ctx.moveTo(oldX,oldY);
	oldX = touch._x;//pageX;
	oldY = touch._y;//pageY;
	ctx.lineTo(oldX,oldY);
	ctx.stroke();
	ctx.moveTo(oldX,oldY);
	_points[_points.length] = new Point(oldX,oldY);
    }, false);

    canvas.addEventListener('mousemove', function(e) {
	if (!isMouseDown) {
	    return;
	}
	get_pos(e);
	if (oldX - e._x < 3 && oldX - e._x > -3) {
	    return;
	}
	if (oldY - e._y < 3 && oldY - e._y > -3) {
	    return;
	}
	oldX = e._x;
	oldY = e._y;

	ctx.lineTo(oldX,oldY);
	ctx.stroke();
	ctx.moveTo(oldX,oldY);
	_points[_points.length] = new Point(oldX,oldY);
    }, false);


    // Ok, now we reach an end. The user release the presure
    canvas.addEventListener('touchend', function(e) {
	ctx.closePath();
	if (_points.length >= 10) {
	    var result = _r.Recognize(_points);
	    //alert(result.Name + Math.round(result.Score*100) + "%");
	    launch_gesture(result.Name, Math.round(result.Score*100));
	}
	_points = [];
	ctx.clearRect(0,0,canvas.width,canvas.height);
    }, false);


    canvas.addEventListener('mouseup', function(e) {
	isMouseDown = false;
	ctx.closePath();
	if (_points.length >= 10) {
	    var result = _r.Recognize(_points);
	    //alert(result.Name + Math.round(result.Score*100) + "%");
	    launch_gesture(result.Name, Math.round(result.Score*100));
	}
	_points = [];
	ctx.clearRect(0,0,canvas.width,canvas.height);
    }, false);

});

/* Look for gesture but launch them only
if we reach a score to be sure :)*/
/* cf : http://depts.washington.edu/aimgroup/proj/dollar/ for
 source */
function launch_gesture(gesture, score){
    if(score >= 60){
	//alert(gesture+' '+score);
	/* Gestures :
	   reactange or circle : recheck now
	   v or 'check' : acknowledge
	   'zig-zag' or 'right curly brace' or left one : try to fix
	 */
	if(gesture == 'rectange' || gesture == 'circle'){
	    recheck_now(elt_name);
	}
	if(gesture == 'v' || gesture == 'check'){
	    ackno_element = elt_name;
	    do_acknowledge('Acknowledged by WebUI gesture.');
	}
	if(gesture == 'zig-zag' || gesture == 'left curly brace' || gesture == 'right curly brace'){
	    try_to_fix(elt_name);
	}
    }
}



