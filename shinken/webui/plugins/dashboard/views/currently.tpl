%rebase layout globals(), js=['dashboard/js/widgets.js', 'dashboard/js/jquery.easywidgets.js', 'dashboard/js/jquery.jclock.js'], css=['dashboard/css/shinken-currently.css'], title='Shinken currently', menu_part='/dashboard', print_header=False, print_footer=False

%from shinken.bin import VERSION
%helper = app.helper

<script type="text/javascript">
/* We are saving the global context for theses widgets */
widget_context = 'dashboard';
</script>

<script type="text/javascript">
$(function($) {
  var options1 = {
        format: '%I %M %S %p' // 12-hour
      }
      $('#clock').jclock(options1);

      var options6 = {
        format: '%A, %B %d'
      }
      $('#date').jclock(options6);

    });
</script>

<!-- Jet Pack Area START -->
<div class="span12">
  <p><span id="clock"></span></p>
  <p><span id="date"></span></p>
</div>
<!-- Jet Pack Area END -->

<div class="span12"> 
  <ul id="Navigation" class="span8 wtf">
    <li class="span3">
      <svg version="1.0" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xlink="http://www.w3.org/1999/xlink" x="0px" y="0px" width="100px" height="85px" viewBox="0 0 100 83.419" enable-background="new 0 0 100 83.419" fill ="#FFFFFF" xml:space="preserve">
        <path fill-opacity="0.875" d="M68.2,55.555l4.742,4.792c6.451-6.143,10.461-14.861,10.461-24.532c0-9.521-3.901-18.122-10.184-24.25
        l-5.159,5.356c5.06,4.861,8.228,11.724,8.228,19.317C76.288,43.797,73.217,50.701,68.2,55.555z"></path>
        <path fill-opacity="0.875" d="M56.625,43.85l5.856,5.923c3.591-3.371,5.857-8.176,5.857-13.535c0-5.425-2.322-10.297-5.996-13.676
        l-5.858,6.063c2.083,1.862,3.486,4.559,3.486,7.613C59.971,39.257,58.664,41.993,56.625,43.85z"></path>
        <path fill-opacity="0.875" d="M20.082,7.333l-5.996-6.063C5.388,10.352,0,22.63,0,36.237c0,13.575,5.286,25.895,13.945,34.967
        l6.137-6.203C12.987,57.483,8.646,47.283,8.646,36.097C8.646,24.914,12.987,14.819,20.082,7.333z"></path>
        <path fill-opacity="0.875" d="M78.66,66.129l6.137,6.202C94.124,63.162,100,50.43,100,36.237C100,21.979,94.071,9.186,84.658,0
        L78.66,6.064c7.797,7.588,12.691,18.201,12.691,30.032C91.352,47.896,86.418,58.51,78.66,66.129z"></path>
        <path fill-opacity="0.875" d="M25.661,12.972c-5.5,6.013-8.926,14.014-8.926,22.843c0,9.017,3.499,17.218,9.205,23.266l4.742-4.796
        c-4.303-4.749-6.974-11.085-6.974-18.047c0-6.996,2.628-13.424,6.974-18.19L25.661,12.972z"></path>
        <path fill-opacity="0.875" d="M42.258,42.583c-1.398-1.747-2.23-3.93-2.23-6.346c0-2.48,0.897-4.718,2.371-6.486l-5.858-5.779
        c-2.938,3.268-4.882,7.514-4.882,12.265c0,4.718,1.84,9.005,4.743,12.268L42.258,42.583z"></path>
        <path d="M45.838,36.237c0,2.324,1.865,4.208,4.16,4.208c2.298,0,4.159-1.884,4.159-4.208c0-2.321-1.861-4.204-4.159-4.204
        C47.703,32.033,45.838,33.917,45.838,36.237z"></path>
        <path fill-opacity="0.875" d="M45.313,46.234L34.497,83.419h30.286L53.966,46.234C51.102,46.874,48.226,47.098,45.313,46.234z"></path>
      </svg>
     <!-- <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" id="Calque_1" x="0px" y="0px" width="100px" height="84.4202898551px" viewBox="0 0 276.252 233.625" enable-background="new 0 0 276.252 233.625" fill="#FFFFFF" xml:space="preserve">
        <g>
          <path d="M150.59,45.375c12.504,0,22.693-10.143,22.693-22.677C173.284,10.173,163.094,0,150.59,0   c-12.56,0-22.707,10.173-22.707,22.698C127.884,35.232,138.031,45.375,150.59,45.375z"/>
          <path d="M145.064,197.108c-3.314,2.213-8.893,6.08-8.893,6.08l-2.761,6.633l-3.863,4.416h-7.19l-17.175,12.76h171.071l-7.735-7.761   l-6.131-6.105l-9.942,0.554l-6.629-7.182c0,0-4.974-8.288-4.974-9.969c0-1.655,1.11-7.765-0.557-8.837   c-1.655-1.132-7.225-4.45-7.225-4.45l-13.262,0.554l-7.228-8.837l-7.19-9.973l-8.841-1.681c0,0-5.569,0.553-7.73,3.314   c-2.26,2.786-7.229,4.994-12.202,7.229c-1.391,0.618-2.825,1.323-4.175,2.018l-66.913-54.536l32.312-62.644l-32.649-47.063H36.526   l-9.02,46.124L14.173,46.885c-2.863-2.31-7.029-1.91-9.394,0.953c-2.31,2.863-1.855,7.033,1.013,9.343l25.878,21.096L15.373,95.88   l1.217,61.397L0.465,216.875c-1.915,7.08,2.259,14.389,9.338,16.295c1.153,0.307,2.357,0.455,3.463,0.455   c5.88,0,11.253-3.893,12.861-9.819l17.074-63.286l2.604-47.849l33.964,40.089l-31.692,58.465   c-3.467,6.48-1.106,14.543,5.369,18.031c2.013,1.106,4.174,1.608,6.335,1.608c4.718,0,9.288-2.511,11.696-6.956l40.286-74.412   l-16.152-19.094l66.632,54.318l-4.475,6.262C157.768,190.982,148.377,194.879,145.064,197.108z M86.666,105.97L72.921,94.767   l25.636-11.169L86.666,105.97z M52.591,35.985l16.584,2.208L47.622,60.342L52.591,35.985z"/>
        </g>
      </svg>-->
      <span class="badger-title itproblem">IT Problems</span>
      %if app:
      %overall_itproblem = app.datamgr.get_overall_it_state()
      %if overall_itproblem == 0:
      <span class=" badger-big badger-ok">OK!</span>
      %elif overall_itproblem == 1:
      <span class="badger-big badger-warning">{{app.datamgr.get_nb_all_problems()}}</span>
      %elif overall_itproblem == 2:
      <span class=" badger-big badger-critical">{{app.datamgr.get_nb_all_problems()}}</span>
      %end
      %end
    </li>

    <li class="span3">
      <svg version="1.0" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
      width="100px" height="82.922px" viewBox="0 0 100 82.922" enable-background="new 0 0 100 82.922" fill="#FFFFFF" xml:space="preserve">
      <path d="M77.958,11.073c-3.73,0-7.339,0.933-10.544,2.685C63.515,5.537,55.108,0,45.693,0C32.842,0,22.314,10.141,21.694,22.838
      c-5.901,0.704-10.96,4.619-13.149,10.09C3.642,34.151,0,38.595,0,43.873c0,6.223,5.062,11.283,11.281,11.283h27.821l-4.238,8.501
      h6.463L28.781,82.922l32.948-23.357l-10.714-0.128l4.004-4.28h22.938c12.154,0,22.042-9.891,22.042-22.042
      C100,20.961,90.112,11.073,77.958,11.073z M77.958,47.375H11.281c-1.932,0-3.502-1.571-3.502-3.502c0-1.904,1.532-3.46,3.43-3.502
      c0.062,0.006,0.125,0.009,0.188,0.012l3.291,0.107l0.65-3.229c0.787-3.915,4.266-6.757,8.266-6.757c0.481,0,0.978,0.044,1.474,0.131
      l5.257,0.924l-0.73-5.284c-0.104-0.766-0.157-1.521-0.157-2.249c0-8.958,7.289-16.244,16.247-16.244
      c7.695,0,14.391,5.462,15.917,12.988l1.405,6.906l5.097-4.871c2.667-2.545,6.163-3.95,9.846-3.95c7.865,0,14.26,6.398,14.26,14.26
      S85.823,47.375,77.958,47.375z"/>
    </svg>
    <span class="badger-title impacts">Impacts</span>
    %if app:
    %overall_state = app.datamgr.get_overall_state()
    %if overall_state == 2:
    <span class="badger-big badger-critical">{{app.datamgr.get_len_overall_state()}}</span>
    %elif overall_state == 1:
    <span class="badger-big badger-critical">{{app.datamgr.get_len_overall_state()}}</span>
    %end
    %end
  </li>
  <li class="span3">
    <svg version="1.0" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
    width="100px" height="82.922px" viewBox="0 0 100 82.922" enable-background="new 0 0 100 82.922" fill="#FFFFFF" xml:space="preserve">
    <path fill-rule="evenodd" clip-rule="evenodd" d="M17.15,47.28V85.2l31.601,13.543v-37.92L17.15,47.28z M84,45.437  L49.653,60.823v37.92L84,83.357V45.437z M61.458,2.445l-33.466,14.83v32.759l9.043,3.747l-0.022-22.753  c0,0,12.31-5.395,24.445-10.691V2.445z M22.575,15.695L22.56,47.784l4.507,1.865V17.485L22.575,15.695z M22.936,14.311l4.484,1.791  l32.759-14.28L55.665,0L22.936,14.311z M38.818,54.525l4.5,1.866V35.543l-4.492-1.791L38.818,54.525z M44.243,56.775l5.41,2.242  l28.057-12.52V20.502l-33.467,14.83V56.775z M39.188,32.368l4.484,1.791l32.76-14.28l-4.515-1.821L39.188,32.368z"/>
  </svg>
  <span class="badger-title services">Services OK</span>
      %if app:
      %service_state = app.datamgr.get_per_service_state()
      %if service_state <= 0:
      <span class="badger-big badger-critical">{{app.datamgr.get_per_service_state()}}%</span>
      %elif service_state <= 33:
      <span class="badger-big badger-critical">{{app.datamgr.get_per_service_state()}}%</span>
      %elif service_state <= 66:
      <span class="badger-big badger-warning">{{app.datamgr.get_per_service_state()}}%</span>
      %elif service_state <= 100:
      <span class="badger-big badger-ok">{{app.datamgr.get_per_service_state()}}%</span>
      %end
      %end
</li>
  <li class="span3">
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" id="Layer_1" x="0px" y="0px" width="100px" height="82.922px" viewBox="0 0 50 50" enable-background="new 0 0 50 50" fill="#FFFFFF" xml:space="preserve">
<polygon points="45.91,26.078 40.467,26.078 40.467,44.177 25.517,44.177 25.517,34.844 16.105,34.844 16.105,44.177 8.73,44.177   8.732,26.078 3.687,26.078 24.596,5.168 "/>
</svg>
  <span class="badger-title hosts">Hosts UP</span>
      %if app:
      %service_state = app.datamgr.get_per_hosts_state()
      %if service_state <= 0:
      <span class="badger-big badger-critical">{{app.datamgr.get_per_hosts_state()}}%</span>
      %elif service_state <= 33:
      <span class="badger-big badger-critical">{{app.datamgr.get_per_hosts_state()}}%</span>
      %elif service_state <= 66:
      <span class="badger-big badger-warning">{{app.datamgr.get_per_hosts_state()}}%</span>
      %elif service_state <= 100:
      <span class="badger-big badger-ok">{{app.datamgr.get_per_hosts_state()}}%</span>
      %end
      %end
</li>
</ul>

</div>

<!-- Shinken Info End -->