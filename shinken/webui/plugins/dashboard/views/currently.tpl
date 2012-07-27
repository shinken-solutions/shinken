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

<?xml version="1.0" encoding="utf-8"?>
<!-- Generator: Adobe Illustrator 14.0.0, SVG Export Plug-In . SVG Version: 6.00 Build 43363)  -->
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.0//EN" "http://www.w3.org/TR/2001/REC-SVG-20010904/DTD/svg10.dtd">
<svg version="1.0" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
width="100px" height="95.105px" viewBox="0 0 100 95.105" enable-background="new 0 0 100 95.105" fill="#FFFFFF  " xml:space="preserve">
<polygon points="50,0 61.803,36.327 100,36.327 69.098,58.778 80.902,95.105 50,72.654 19.098,95.105 30.902,58.778 0,36.327 
38.197,36.327 "/>
</svg>





<div class="span12"> 
  <ul id="Navigation">
    <li>
      <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" id="Calque_1" x="0px" y="0px" width="100px" height="84.4202898551px" viewBox="0 0 276.252 233.625" enable-background="new 0 0 276.252 233.625" fill="#FFFFFF" xml:space="preserve">
        <g>
          <path d="M150.59,45.375c12.504,0,22.693-10.143,22.693-22.677C173.284,10.173,163.094,0,150.59,0   c-12.56,0-22.707,10.173-22.707,22.698C127.884,35.232,138.031,45.375,150.59,45.375z"/>
          <path d="M145.064,197.108c-3.314,2.213-8.893,6.08-8.893,6.08l-2.761,6.633l-3.863,4.416h-7.19l-17.175,12.76h171.071l-7.735-7.761   l-6.131-6.105l-9.942,0.554l-6.629-7.182c0,0-4.974-8.288-4.974-9.969c0-1.655,1.11-7.765-0.557-8.837   c-1.655-1.132-7.225-4.45-7.225-4.45l-13.262,0.554l-7.228-8.837l-7.19-9.973l-8.841-1.681c0,0-5.569,0.553-7.73,3.314   c-2.26,2.786-7.229,4.994-12.202,7.229c-1.391,0.618-2.825,1.323-4.175,2.018l-66.913-54.536l32.312-62.644l-32.649-47.063H36.526   l-9.02,46.124L14.173,46.885c-2.863-2.31-7.029-1.91-9.394,0.953c-2.31,2.863-1.855,7.033,1.013,9.343l25.878,21.096L15.373,95.88   l1.217,61.397L0.465,216.875c-1.915,7.08,2.259,14.389,9.338,16.295c1.153,0.307,2.357,0.455,3.463,0.455   c5.88,0,11.253-3.893,12.861-9.819l17.074-63.286l2.604-47.849l33.964,40.089l-31.692,58.465   c-3.467,6.48-1.106,14.543,5.369,18.031c2.013,1.106,4.174,1.608,6.335,1.608c4.718,0,9.288-2.511,11.696-6.956l40.286-74.412   l-16.152-19.094l66.632,54.318l-4.475,6.262C157.768,190.982,148.377,194.879,145.064,197.108z M86.666,105.97L72.921,94.767   l25.636-11.169L86.666,105.97z M52.591,35.985l16.584,2.208L47.622,60.342L52.591,35.985z"/>
        </g>
      </svg>
    </li>

    <li>
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
    <span class="badger-big badger-critical">8</span>
  </li>
</ul>

</div>
%if app:
%overall_state = app.datamgr.get_overall_state()
%if overall_state == 2:
<li><a href="/impacts" class="quickinfo" data-original-title='Impacts'><i class="icon-impact"></i><span class="pulsate badger badger-critical">{{app.datamgr.get_len_overall_state()}}</span> </a></li>
%elif overall_state == 1:
<li><a href="/impacts" class="quickinfo" data-original-title='Impacts'><i class="icon-impact"></i><span class="pulsate badger badger-warning">{{app.datamgr.get_len_overall_state()}}</span> </a></li>
%end
%end
<!-- Shinken Info Start -->
<div id="footer" class="span12">
  <p>Version: {{VERSION}}</p>
</div>



<!-- Shinken Info End -->