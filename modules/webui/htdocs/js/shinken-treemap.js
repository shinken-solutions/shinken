


var _colors = ['7FCAFF', '7F97FF', 'A77FFF', 'E77FFF', 'FF7FB0', 'FF9C7E', 'FFBD7E', 'FFD77E',
	      'FFF17E', 'F3FF7E', 'CAF562', '62F5C8', '7FCAFF', '83C5D1', 'B2D9D6', '798287',
	      'C3D7BF', 'C7DAD4', 'FCD6E1', 'F0E5E1', 'E3E2F0', 'F1D9FB'];

function get_color() {
    return '#'+_colors[Math.floor(Math.random() * _colors.length)];
}



function add_treemap(tree){

    var tm = new $jit.TM.Squarified({  
	//where to inject the visualization  
	injectInto: 'treemap',  
	//parent box title heights  
	titleHeight: 15,  
	//enable animations  
	animate: true,
	//box offsets  
	offset: 1,  
	//Attach left and right click events  
	Events: {  
            enable: true,  
            onClick: function(node) {  
		if(node) tm.enter(node);  
            },  
            onRightClick: function() {  
		tm.out();  
            }  
	},  
	duration: 500,  
	//Enable tips  
	Tips: {  
            enable: true,  
            //add positioning offsets  
            offsetX: 20,  
            offsetY: 20,  
            //implement the onShow method to  
            //add content to the tooltip when a node  
            //is hovered  
            onShow: function(tip, node, isLeaf, domElement) {  
		var html = "<div class=\"tip-title\">" + node.name   
		    + "</div><div class=\"tip-text\">";  
		var data = node.data;  
		if(data.memory) {  
		    html += "Memory : " + data.memory + '%';  
		}  
		tip.innerHTML =  html;
		tip.className = 'treemap-tip';
            }    
	},  
	//Add the name of the node in the correponding label  
	//This method is called once, on label creation.  
	onCreateLabel: function(domElement, node){  
            domElement.innerHTML = node.name;  
            var style = domElement.style;  
            style.display = '';  
            style.border = '1px solid transparent';  
            domElement.onmouseover = function() {  
		style.border = '1px solid #9FD4FF';  
            };  
            domElement.onmouseout = function() {  
		style.border = '1px solid transparent';  
            };
	    domElement.className = 'treemap-node';
	}  
    });  
    tm.loadJSON(tree);  
    tm.refresh();  
}
