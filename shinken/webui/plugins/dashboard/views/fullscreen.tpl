%rebase layout globals(), js=['dashboard/js/jquery.jclock.js'], css=['dashboard/css/fullscreen.css'], title='Architecture state', menu_part='/dashboard', print_header=False

%from shinken.bin import VERSION
%helper = app.helper

<script type="text/javascript">
    $(function($) {
      var options = {
        format: '%I:%M %p', // 12-hour with am/pm 
      }
      $('.jclock').jclock(options);
    });
</script>
    <script type="text/javascript">
        var settimmer = 0;
        $(function(){
                window.setInterval(function() {
                    var timeCounter = $("span[id=show-time]").html();
                    var updateTime = eval(timeCounter)- eval(1);
                    $("span[id=show-time]").html(updateTime);

                    //if(updateTime == 0){
                    //    window.location = ("redirect.php");
                    //}
                }, 1000);

        });
    </script>


<!-- Dashboard Header START -->
<div id="dash-header" class="span12">
	<ul class="span9 pull-left">
		<li></li>
		<li></li>
	</ul>
	<ul class="span3 pull-right">
		<li style="width: 150px;"><span class="jclock clock"></span></li>
		<li><span id="show-time" class="clock">62</span> </li>
	</ul>
</div>
<!-- Dashboard Header END -->

<!-- Jet Pack Area START -->
<div class="span12">
	<p style="width: 96.5%" class="btn btn-large btn-success no-leftmergin"><span class="pull-left"><i class="icon-fire icon-white"></i> <b>Nothing To Do Here / <span class="jetpack">Jet Pack Guy</span></b></span></p>
</div>
<!-- Jet Pack Area END -->

<!-- Content START -->
<div>
	<div class="span4 hell">
		<h3>IT problems</h3>
	</div>
	<div class="span4 hell">
		<h3>Last IT problems</h3>
	</div>
	<div class="span4 hell">
		<h3>Impacts</h3>
	</div>	
</div>
<!-- Content END -->