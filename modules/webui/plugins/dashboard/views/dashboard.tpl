%rebase layout globals(), js=['dashboard/js/widgets.js', 'dashboard/js/jquery.easywidgets.js'], css=['dashboard/css/widget.css', 'dashboard/css/dashboard.css'], title='Dashboard', menu_part='/dashboard', refresh=True

%from shinken.bin import VERSION
%helper = app.helper

<script>
  /* We are saving the global context for theses widgets */
  widget_context = 'dashboard';
</script>

<!-- Maybe the admin didn't add a user preference module, or the module is dead, if so, warn about it -->
%if not has_user_pref_mod:
<div id="warn-pref" class="hero-unit alert-critical">
  <h2>Warning:</h2>
  <p>You didn't define a WebUI module for saving user preferences like the MongoDB one. You won't be able to use this page!</p>
  <p><a href="http://www.shinken-monitoring.org/wiki/shinken_10min_start" class="btn btn-success btn-large">Learn more <i class="icon-hand-right"></i></a></p>
</div>
%end

<div class="row">
  <div id="loading" class="pull-left"> <img src='/static/images/spinner.gif'> Loading widgets</div>
  %# If we got no widget, we should put the button at the center fo the screen
  %small_show_panel_s = ''
  %if len(widgets) == 0:
     %small_show_panel_s = 'hide'
  %end
  <a id='small_show_panel' href="#pageslide" class="slidelink btn btn-small btn-success pull-right {{small_show_panel_s}}"><i class="icon-plus"></i> Add a new widget</a>
  %# Go in the center of the page!
  <span id="center-button" class="span4 offset4 page-center" >
    <h3>You don't have any widget yet?</h3>
  <a href="#pageslide" class="slidelink btn btn-large btn-success at-center"><i class="icon-plus"></i> Add a new widget</a>
  </span>
</div>

<div id="pageslide" style="display:none">
    <div class="span12 row">
      <h3 class="span10 pull-left font-white">Widgets available</h3>
      <p class="span2 pull-right"><a class="btn btn-small btn-danger" href="javascript:$.pageslide.close()"><i class="icon-remove"></i> Close</a></p>
    </div>
      <p>&nbsp;</p>
      <p>&nbsp;</p>
    <div class='row span12'>
    %for w in app.get_widgets_for('dashboard'):
    <div class='widget_desc span5' style='position: relative;'>
      <div class='row-fluid'>
	<span class="span4" style="margin-top:10px;">
	  <img class="img-rounded" style="width:64px;height:64px" src="{{w['widget_picture']}}" id="widget_desc_{{w['widget_name']}}"/>
	</span>
	<span class='span6'>
	  {{!w['widget_desc']}}
	</span>
      </div>
      <p class="add_button"><a class='btn btn-mini btn-success' href="javascript:AddNewWidget('{{w['base_uri']}}', 'widget-place-1');"> <i class="icon-chevron-left"></i> Add {{w['widget_name']}} widget</a></p>
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
