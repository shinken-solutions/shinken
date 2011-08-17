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


window.onload = function init(){
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
			//'shadowBlur': 50,
			//'shadowColor': '#ccc'
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
		//Change other animation parameters.
		duration:1000,
		fps: 30,
		//Change father-child distance.
		levelDistance: 100,
		//This method is called right before plotting
		//an edge. This method is useful to change edge styles
		//individually.
		onBeforePlotLine: function(adj){
		    //Add some random lineWidth to each edge.
		    if (!adj.data.$lineWidth)
			adj.data.$lineWidth = 2;
		},

		onBeforeCompute: function(node){
		    Log.write("Focusing on " + node.name + "...");

		    //Make right column relations list.
		    var html = "<h4>" + node.name + "</h4><b>Connections:</b>";
		    html += "<ul>";
		    node.eachAdjacency(function(adj){
			    var child = adj.nodeTo;
			    html += "<li>" + child.name + "</li>";
			});
		    html += "</ul>";
		    $jit.id('inner-details').innerHTML = html;
		},
		//Add node click handler and some styles.
		//This method is called only once for each node/label crated.
		onCreateLabel: function(domElement, node){
		    domElement.innerHTML = node.name;
		    domElement.onclick = function () {
			rgraph.onClick(node.id, {
				hideLabels: false,
				onComplete: function() {
				    Log.write("done");
				}
			    });
		    };
		    var style = domElement.style;
		    style.cursor = 'pointer';
		    style.fontSize = "0.8em";
		    style.color = "#fff";
		},
		//This method is called when rendering/moving a label.
		//This is method is useful to make some last minute changes
		//to node labels like adding some position offset.
		onPlaceLabel: function(domElement, node){
		    var style = domElement.style;
		    var left = parseInt(style.left);
		    var w = domElement.offsetWidth;
		    style.left = (left - w / 2) + 'px';
		}
	    });
	//load graph.
	rgraph.loadJSON(json, 1);
	rgraph.root =  'localhost';
	//compute positions and plot
	rgraph.refresh();
	//end
	//alert('Roto is'+rgraph.root);
	//rgraph.root =  graph.get('localhost');
	rgraph.controller.onBeforeCompute(rgraph.graph.getNode(rgraph.root));
	Log.write('done');

}


//window.addEvent('domready',init());