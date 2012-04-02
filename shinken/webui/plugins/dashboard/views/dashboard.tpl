%rebase layout globals(), js=['dashboard/js/jquery.easywidgets.js', 'dashboard/js/jquery.pageslide.js'], css=['dashboard/css/widget.css', 'dashboard/css/jquery.pageslide.css'], title='Dashboard', menu_part='/dashboard'

%from shinken.bin import VERSION
%helper = app.helper


<script type="text/javascript">
$(function(){

  // where we stock all current widgets loaded, and their options
  widgets = [];

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
    },

   callbacks : {
      onCollapse : function(link, widget){
          var name = widget.attr('id');
          var key = name+'_collapsed';
          $.post("/user/save_pref", { 'key' : key, 'value' : true});
      },
      onExtend : function(link, widget){
        alert('onentend callback :: Link: ' + link + ' - Widget: ' + widget.attr('id'));
      }

   }
  });
  
});
</script>



<p><a href="#pageslide" class="slidelink">Add a new widget</a></p>
<div id="pageslide" style="display:none">
    <h2>Widgets available</h2>
    
    <a href="javascript:AddNewWidget('/widget/system', 'widget-place-1');"> Add system widget</a>
    <a href="javascript:$.pageslide.close()">Close</a>
</div>
<script >$(function(){
  $(".slidelink").pageslide({ direction: "left", modal : true});
  });
</script>



<script>

  function save_new_widgets(){
     var widgets_ids = [];
     var save_widgets_list = false;
     $.each(widgets, function(idx, w){
         var o = {'id' : w.id, 'position' : w.position, 'base_url' : w.base_url, 'options' : w.options};
         widgets_ids.push(o);
         if(!w.hasOwnProperty('is_saved')){
           save_widgets_list = true;
           //alert('Saving widget'+w.id);
           var key= 'widget_'+w.id;
           var value = JSON.stringify(w);
           alert('with key:value'+key+' '+value);
           $.post("/user/save_pref", { 'key' : key, 'value' : value});
           w.is_saved=true;
         }
     });

     // Look if weneed to save the widget lists
     if(save_widgets_list){
         alert('Need to save widgets list'+JSON.stringify(widgets_ids));
         $.post("/user/save_pref", { 'key' : 'widgets', 'value' : JSON.stringify(widgets_ids)});
     }

  }

  setInterval( save_new_widgets, 1000);


  // Now try to load widgets in a dynamic way
  function AddWidget(url, placeId){
    $.get(url, function(html){
      $.fn.AddEasyWidget(html, placeId, {});
    });
  }

  // when we add a new widget, we also save the current widgets
  // configuration for this user
  function AddNewWidget(url, placeId){
      AddWidget(url, placeId) ;
  }

  // Now load the system as example
  $(function(){
      %for w in widgets:
         %if 'base_url' in w and 'position' in w:
            %uri = w['base_url'] + "?" + w['options_uri']
            AddWidget("{{uri}}", "{{w['position']}}");
         %end
      %end
      //AddWidget('/widget/system', 'widget-place-1');
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
