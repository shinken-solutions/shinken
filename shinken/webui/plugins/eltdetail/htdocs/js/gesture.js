var oldX; var oldY;
var canvas;
var ctx;
var _r = new DollarRecognizer();
var _points = [];
var isMouseDown = false; // mouse only bool
var threshold = 3; // number of pixels required to be moved for a movement to count


document.addEventListener('touchstart', function(e) {
	e.preventDefault();
	_points = [];
	var touch = e.touches[0];
	ctx.beginPath();
	ctx.strokeStyle = "#bae1ff";
	ctx.lineCap = "round";
	ctx.lineJoin = "round";
	ctx.lineWidth = 6;
	oldX = touch.pageX;
	oldY = touch.pageY;
    }, false);

document.addEventListener('touchmove', function(e) {
	if (oldX - e.pageX < 3 && oldX - e.pageX > -3) {
	    return;
	}
	if (oldY - e.pageY < 3 && oldY - e.pageY > -3) {
	    return;
	}
	var touch = e.touches[0];
	ctx.moveTo(oldX,oldY);
	oldX = touch.pageX;
	oldY = touch.pageY;
	ctx.lineTo(oldX,oldY);
	ctx.stroke();
	ctx.shadowColor = 'rgba(169,236,255,0.25)';
	ctx.shadowOffsetX = 0;
	ctx.shadowOffsetY = 0;
	ctx.shadowBlur = 10;
	_points[_points.length] = new Point(oldX,oldY);
    }, false);

document.addEventListener('touchend', function(e) {
	ctx.closePath();
	if (_points.length >= 10) {
	    var result = _r.Recognize(_points);
	    $("#shapeOutput").text(result.Name);
	    $("#mathOutput").text(Math.round(result.Score*100) + "%");
	}
	_points = [];
	ctx.clearRect(0,0,canvas.width,canvas.height);
    }, false);


window.addEventListener("load", function(e) {
	canvas = document.getElementById("canvas");  
	ctx = canvas.getContext("2d");
	canvas.width = window.innerWidth;
	canvas.height = window.innerHeight;
    }, false);




// MOUSE BINDS FOR THE HELL OF IT
document.addEventListener('mousedown', function(e) {
	isMouseDown = true;
	e.preventDefault();
	_points = [];
	ctx.beginPath();
	ctx.strokeStyle = "#bae1ff";
	ctx.lineCap = "round";
	ctx.lineJoin = "round";
	ctx.lineWidth = 6;
	ctx.shadowColor = 'rgba(169,236,255,0.1)';
	ctx.shadowOffsetX = 0;
	ctx.shadowOffsetY = 0;
	ctx.shadowBlur = 10;
	oldX = e.pageX;
	oldY = e.pageY;
    }, false);

document.addEventListener('mousemove', function(e) {
	if (!isMouseDown) {
	    return;
	}
	if (oldX - e.pageX < 3 && oldX - e.pageX > -3) {
	    return;
	}
	if (oldY - e.pageY < 3 && oldY - e.pageY > -3) {
	    return;
	}
	ctx.moveTo(oldX,oldY);
	oldX = e.pageX;
	oldY = e.pageY;
	ctx.lineTo(oldX,oldY);
	ctx.stroke();
	_points[_points.length] = new Point(oldX,oldY);
    }, false);

document.addEventListener('mouseup', function(e) {
	isMouseDown = false;
	ctx.closePath();
	if (_points.length >= 10) {
	    var result = _r.Recognize(_points);
	    /*alert(result.Name + Math.round(result.Score*100) + "%");*/
	    launch_gesture(result.Name, Math.round(result.Score*100));
	    /*$("shapeOutput").text(result.Name);
	      $("mathOutput").text(Math.round(result.Score*100) + "%");*/
	}
	_points = [];
	ctx.clearRect(0,0,canvas.width,canvas.height);
    }, false);


/* Look for gesture but launch them only
if we reach a score to be sure :)*/
/* cf : http://depts.washington.edu/aimgroup/proj/dollar/ for
 source */
function launch_gesture(gesture, score){
    if(score >= 60){
	//alert(gesture+' '+score);
	/* Gestures :
	   reactange or circle : recheck now
	   v or 'check' : acknoledge
	   'zig-zag' or 'right curly brace' or left one : try to fix
	 */
	if(gesture == 'rectange' || gesture == 'circle'){
	    recheck_now(elt_name);
	}
	if(gesture == 'v' || gesture == 'check'){
	    ackno_element = elt_name;
	    do_acknoledge('Acknoledged by WebUI gesture.');
	}
	if(gesture == 'zig-zag' || gesture == 'left curly brace' || gesture == 'right curly brace'){
	    try_to_fix(elt_name);
	}
    }
}