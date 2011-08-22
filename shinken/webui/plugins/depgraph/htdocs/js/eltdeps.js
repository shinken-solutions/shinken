var labelType, useGradients, nativeTextSupport, animate;

(function() {
    var ua = navigator.userAgent,
	iStuff = ua.match(/iPhone/i) || ua.match(/iPad/i),
	typeOfCanvas = typeof HTMLCanvasElement,
	nativeCanvasSupport = (typeOfCanvas == 'object' || typeOfCanvas == 'function'),
	      textSupport = nativeCanvasSupport
	&& (typeof document.createElement('canvas').getContext('2d').fillText == 'function');
    //I'm setting this based on the fact that ExCanvas provides text support for IE
    //and that as of today iPhone/iPad current text support is lame
    labelType = (!nativeCanvasSupport || (textSupport && !iStuff))? 'Native' : 'HTML';
    nativeTextSupport = labelType == 'Native';
    useGradients = nativeCanvasSupport;
    animate = !(iStuff || !nativeCanvasSupport);
})();

var Log = {
    elem: false,
    write: function(text){
	if (!this.elem)
	    this.elem = document.getElementById('log');
	this.elem.innerHTML = text;
	this.elem.style.left = (500 - this.elem.offsetWidth / 2) + 'px';
    }
};


function init(){
    //init data
    //If a node in this JSON structure
    //has the "$type" or "$dim" parameters
    //defined it will override the "type" and
    //"dim" parameters globally defined in the
    //RGraph constructor.
        var json = [
		    {
			"id": "Mem",
			"name": "Mem",
			"data": {
			    "$dim": 5,
			    "$type": "star",
			    "$color":"red",
			    "some other key": "some other value"
			},
			"adjacencies": [{
				"nodeTo": "localhost",
				"data": {
				    "$type":"arrow",
				    "$color":"red",
				    "weight": 3,
				    "$direction": ["Mem", "localhost"],
				}
			    }]
		    },


		    {
			"id": "localhost",
			"name": "localhost",
			"data": {
			    "$color":"red",
			    "$dim": 5*2,
			    "some other key": "some other value"
			},
			"adjacencies": [{
				"nodeTo": "main router",
				"data": {
				    "$type":"arrow",
				    "$color":"gray",
				    "weight": 3,
				    "$direction": ["localhost", "main router"],
				}
			    }
			            ]
		    },{
			"id": "main router",
			"name": "main router",
			"data": {
			    //"$dim": 32.26403873194912,
			    //"$type": "star",
			    "$color":"green",
			    "some other key": "some other value"
			},
			"adjacencies": []
		    }
		    ,{
			"id": "CPU",
			"name": "CPU",
			"data": {
			    //"$dim": 32.26403873194912,
			    "$type": "star",
			    "$dim": 5*2,
			    "$color":"red",
			    "some other key": "some other value"
			},
			"adjacencies": [{
				"nodeTo": "localhost",
				"data": {
				    "$type":"arrow",
				    "$color":"red",
				    "weight": 3,
				    "$direction": ["CPU", "localhost"],
				}
			    }]
		    }
		    ];
	//end
	//init RGraph
	var rgraph = new $jit.RGraph({
		'injectInto': 'infovis',
		//Optional: Add a background canvas
		//that draws some concentric circles.
		'background': {
		    'CanvasStyles': {
			'strokeStyle': '#555',
			'shadowBlur': 50,
			'shadowColor': '#ccc'
		    }
		},
		//Add navigation capabilities:
		//zooming by scrolling and panning.
		Navigation: {
		    enable: true,
		    panning: true,
		    zooming: 20
		},
		//Nodes and Edges parameters
		//can be overridden if defined in
		//the JSON input data.
		//This way we can define different node
		//types individually.
		Node: {
		    color: '#ddeeff',
		    'overridable': true,
		},
		Edge: {
		    color: '#C17878',
		    lineWidth:1.5,
		    'overridable': true,
		},
		//Set polar interpolation.
		//Default's linear.
		interpolation: 'polar',
		//Change the transition effect from linear
		//to elastic.
		//transition: $jit.Trans.Elastic.ea