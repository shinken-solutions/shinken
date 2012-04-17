%rebase layout globals(), js=['dashboard/js/widgets.js', 'dashboard/js/jquery.easywidgets.js'], css=['dashboard/css/widget.css', 'dashboard/css/dashboard.css'], title='Dashboard', menu_part='/dashboard'

%from shinken.bin import VERSION
%helper = app.helper


<div class='span12'>
  <div id='loading' class='pull-left'> <img src='/static/images/spinner.gif'> Loading widgets</div>
  <a href="#pageslide" class="slidelink btn btn-success pull-right"><i class="icon-plus"></i> Add a new widget</a>
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
    <div class='widget_desc span5'>
      {{!w['widget_desc']}}
      <p>&nbsp;</p>
      <p><a class='btn btn-success' href="javascript:AddNewWidget('{{w['base_uri']}}', 'widget-place-1');"> <i class="icon-chevron-left"></i> Add {{w['widget_name']}} widget</a></p>
    </div>
    %end
    </div>

    

</div>

<script >$(function(){
  $(".slidelink").pageslide({ direction: "left", modal : true});
  });
</script>



<script>
  // Now load the system as example
  $(function(){
      %for w in widgets:
         %if 'base_url' in w and 'position' in w:
            %uri = w['base_url'] + "?" + w['options_uri']
            AddWidget("{{!uri}}", "{{w['position']}}");
            var w = {'id' : "{{w['id']}}", 'base_url' : "{{w['base_url']}}", 'position' : "{{w['position']}}", 'options' : JSON.parse('{{w['options']}}')};
            widgets.push(w);
         %end
      %end
      //AddWidget('/widget/system', 'widget-place-1');
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
