%import json

<div id='cv_memory_cont' class='span12'>
  <div id="treemap" class='span11'></div>
  <div  class='span1'> <a  href="javascript:reload_custom_view('memory');"><i class="icon-repeat"></i> Reload</a></div>
  
</div>


<link href="/static/cv_memory/css/memory.css" rel="stylesheet">


<script>

  loadjscssfile('/static/depgraph/js/jit-yc.js', 'js');
  loadjscssfile('/static/cv_memory/js/memory.js', 'js');

  ps = {{json.dumps(ps)}};


    var used_mem = 0.0;
    var tree = {
        "children": [],
        "data": {},
        "id": "root",
        "name": "Memory usage"
    };

    for(i=0; i<ps.length;i++){
      var p = ps[i];
      used_mem += p['memory_percent'];
      console.log('Useed mem? : ' + used_mem);
      cmd = p['cmdline'];
      var _t = {
                "children": [],
                "data": {
                    "memory": p['memory_percent'],
                    "$color": get_color(),
                    "$area": p['memory_percent']
                },
                "id": 'pid'+p['pid'],
                "name": p['cmdline']
            };
      tree["children"].push(_t);
    }

    


    // Now add the free one
    tree["children"].push({"children": [],
                "data": {
                    "memory": 100 - used_mem,
                    "$color": '#669900',
                    "$area": 100 - used_mem
                },
                "id": "(free)",
                "name": "(free)"
            });

 console.log(tree);


function launch_memory_tree_map(tree){
  if(typeof $jit === "undefined"){
      console.log('Warning : there is no $jit, I postpone my init for 1s');
      // Still not load $jit? racing problems are a nightmare :)
      // Ok, we retry in the next second...
      setTimeout(function(){launch_memory_tree_map(tree)},1000);
     return;
    }
  console.log("JIT IS HERE");
  add_treemap(tree);
}


$(function(){
//  add_treemap(tree);
  launch_memory_tree_map(tree);
});

</script>


