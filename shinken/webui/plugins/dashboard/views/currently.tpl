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

<script type="text/javascript">
var settimmer = 0;
$(function(){
  window.setInterval(function() {
    var timeCounter = $("span[id=show-time]").html();
    var updateTime = eval(timeCounter)- eval(1);
    $("span[id=show-time]").html(updateTime);
  }, 1000);
});
</script>

<!-- Dashboard Header START -->
<!--
<div id="dash-header" class="span12">
  <ul class="span9 pull-left">

    <li></li>
  </ul>
  <ul class="span2 pull-right">
    <li style="width: 150px;"><span class="jclock clock"></span></li>
    <li> <span id="show-time" class="clock">62</span> </li>
    <li> <a id='small_show_panel' href="#pageslide" class="slidelink"></a></li>
    <li> <a href="/dashboard"  class="icon-home"></a></li>
  </ul>
</div>
-->
<!-- Dashboard Header END -->

<!-- Jet Pack Area START -->
<div class="span12">
<p><span id="clock"></span></p>
<p><span id="date"></span></p>
</div>
<!-- Jet Pack Area END -->

<!-- Shinken Info Start -->
<div class="span12"><p>Version: {{VERSION}}</p></div>

<!-- Shinken Info End -->