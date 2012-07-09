%rebase layout globals(), js=['dashboard/js/widgets.js', 'dashboard/js/jquery.easywidgets.js', 'dashboard/js/jquery.jclock.js'], css=['dashboard/css/fullscreen-widget.css', 'dashboard/css/dashboard.css', 'dashboard/css/fullscreen.css'], title='Dashboard', menu_part='/dashboard', print_header=False, print_footer=False

%from shinken.bin import VERSION
%helper = app.helper

<script type="text/javascript">
  /* We are saving the global context for theses widgets */
  widget_context = 'dashboard';
</script>

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
            }, 1000);
    });
</script>

<!-- Dashboard Header START -->
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
<!-- Dashboard Header END -->

<!-- Jet Pack Area START -->
<div class="span12">
  <p style="width: 96.5%" class="btn btn-dash btn-success no-leftmergin"><span class="pull-left"><i class="icon-fire icon-white"></i> <b>Nothing To Do Here / <span class="jetpack">Jet Pack Guy</span></b></span></p>
</div>
<!-- Jet Pack Area END -->

<div class='span12'>
  <div id='loading' class='pull-left'> <img src='/static/images/spinner.gif'> Loading widgets</div>
</div>

<div id="pageslide" style="display:none">
    <div class='row'>
      <h2 class='pull-left'>Widgets available</h2>
      <p class='pull-right'><a class='btn btn-danger' href="javascript:$.pageslide.close()"><i class="icon-remove"></i> Close</a></p>
    </div>
      <p>&nbsp;</p>
      <p>&nbsp;</p>
    <div class='row span12'>
    %for w in app.get_widgets_for('dashboard'):
    <div class='widget_desc span5' style='position: relative;'>
      <div class='row'>
    <span class='span4'>
      <img style="width:64px;height:64px" src="{{w['widget_picture']}}" id="widget_desc_{{w['widget_name']}}"/>
    </span>
    <span class='span6'>
      {{!w['widget_desc']}}
    </span>
    <p>&nbsp;</p>
      </div>
      <p class="add_button"><a class='btn btn-success' href="javascript:AddNewWidget('{{w['base_uri']}}', 'widget-place-1');"> <i class="icon-chevron-left"></i> Add {{w['widget_name']}} widget</a></p>
    </div>
    %end
    </div>
</div>

<script >$(function(){
  $(".slidelink").pageslide({ direction: "left", modal: true});
  });
</script>



<script>
  // Now load all widgets
  $(function(){
      %for w in widgets:
         %if 'base_url' in w and 'position' in w:
            %uri = w['base_url'] + "?" + w['options_uri']
            AddWidget("{{!uri}}", "{{w['position']}}");
            var w = {'id': "{{w['id']}}", 'base_url': "{{w['base_url']}}", 'position': "{{w['position']}}", 'options': JSON.parse('{{w['options']}}')};
            widgets.push(w);
         %end
      %end
  });
</script>

<div class="widget-place" id="widget-place-1">

</div>
<!-- /place-1 -->

<div class="widget-place" id="widget-place-2">

</div>


<div class="widget-place" id="widget-place-3">

</div>

<!-- /place-2 -->


  <!-- End Easy Widgets plugin HTML markup -->




  <!-- Bellow code not is part of the Easy Widgets plugin HTML markup -->

  <div style="clear:both">
