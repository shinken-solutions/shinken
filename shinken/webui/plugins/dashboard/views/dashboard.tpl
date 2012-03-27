%rebase layout globals(), js=['dashboard/js/jquery.easywidgets.js', 'dashboard/js/jquery.pageslide.js'], css=['dashboard/css/widget.css', 'dashboard/css/jquery.pageslide.css'], title='Dashboard', menu_part='/dashboard'

%from shinken.bin import VERSION
%helper = app.helper


<script type="text/javascript">
$(function(){

  // Very basic usage
  
  $.fn.EasyWidgets(	
	{
    effects : {
      effectDuration : 100,
      widgetShow : 'slide',
      widgetHide : 'slide',
      widgetClose : 'slide',
      widgetExtend : 'slide',
      widgetCollapse : 'slide',
      widgetOpenEdit : 'slide',
      widgetCloseEdit : 'slide',
      widgetCancelEdit : 'slide'
    }
  });
  
});
</script>



<p><a href="#pageslide" class="slidelink">Add a new widget</a></p>
<div id="pageslide" style="display:none">
    <h2>Widgets available</h2>
    
    <a href="javascript:$.pageslide.close()">Close</a>
</div>
<script >$(function(){
  $(".slidelink").pageslide({ direction: "left", modal : true});
  });
</script>



<script>
  // Now try to load widgets in a dynamic way
  function AddWidget(url, placeId){
    $.get(url, function(html){
      $.fn.AddEasyWidget(html, placeId, {});
    });
  }

  // Now load the system as example
  $(function(){
     AddWidget('/widget/system', 'widget-place-1');
  });
</script>

<div class="widget-place" id="widget-place-1">

  <div class="widget movable collapsable removable editable closeconfirm" >
    <div class="widget-header">
      <strong>Title</strong>
    </div>
    <div class="widget-editbox">
      Edit the widget here
    </div>
    <div class="widget-content">
      Lorem ipsum dolor sit amet, consectetur adipiscing elit.
      Ut accumsan fringilla turpis. Lorem ipsum dolor.
    </div>
  </div>
</div>
<!-- /place-1 -->

<div class="widget-place" id="widget-place-2">
  <div class="widget movable collapsable removable editable closeconfirm">
    <div class="widget-header">
      <strong>Title</strong>
    </div>
    <div class="widget-editbox">
      Edit the widget here
    </div>
    <div class="widget-content">
      Lorem ipsum dolor sit amet, consectetur adipiscing elit.
      Ut accumsan fringilla turpis. Lorem ipsum dolor.
    </div>
  </div>


  <div class="widget movable collapsable removable editable closeconfirm">
    <div class="widget-header">
      <strong>Widget 3</strong>
    </div>
    <div class="widget-editbox">
      Edit the widget here
    </div>
    <div class="widget-content">
      Here you can put what you want
    </div>
  </div>


</div>
<!-- /place-2 -->


  <!-- End Easy Widgets plugin HTML markup -->




  <!-- Bellow code not is part of the Easy Widgets plugin HTML markup -->

  <div style="clear:both">
