%import json

<script>
  all_perfs = {{json.dumps(all_perfs)}}
  all_disks = all_perfs['all_disks'];
  all_states = {{json.dumps(all_states)}}; //{"disks": "warning", "global": "critical", "agent": "critical", "swap": "ok", "memory": "ok", "cpu": "ok"};
  console.log(all_states);

loadjscssfile('/static/cv_linux/js/host_canvas.js', 'js');
loadjscssfile('/static/cv_linux/css/host_canvas.css', 'css');
</script>

<div class='span1' id='host_linux_bloc'>
  <canvas id='host_canvas' width='600' height='300' data-global-state="{{all_states['global']}}" data-hname='{{elt.get_name()}}' data-icon-uri="{{app.helper.get_icon_state(elt)}}" ></canvas>

  %pct_cpu = all_perfs['cpu']
  <div class="donutContainer" id='donut_cpu'>
    <canvas data-value={{pct_cpu}} data-state="{{all_states['cpu']}}" id="donut-cpu" class='donut_canvas' width="100" height="110"></canvas>
    <span class="counter">{{pct_cpu}}%</span>
    <span class="lab">Cpu</span>
  </div>

  <div id='memory_cylinders'>
    %pct_memory = all_perfs['memory']
    <canvas data-value={{pct_memory}} data-state="{{all_states['memory']}}" id="cylinder_mem" class='cylinder_canvas' width="30" height="100"></canvas>
    <span class="cylinder_label mem_label">Mem</span>
    <span class="cylinder_value mem_value">{{pct_memory}}%</span>
    %pct_swap = all_perfs['swap']
    <canvas data-value={{pct_swap}} data-state="{{all_states['swap']}}" id="cylinder_swap" class='cylinder_canvas' width="30" height="100"></canvas>
    <span class="cylinder_label swap_label">Swap</span>
    <span class="cylinder_value swap_value">{{pct_swap}}%</span>
  </div>

</div>


<script>
  $(function(){
     register_all_donuts();
     register_all_cylinders();
  });
</script>
