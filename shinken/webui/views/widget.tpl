
%# Load all css stuff we need
%if not 'css' in locals(): css = []
%if not 'js' in locals(): js = []

<script type="text/javascript">
function loadjscssfile(filename, filetype){
 if (filetype=="js"){ //if filename is a external JavaScript file
  var fileref=document.createElement('script')
  fileref.setAttribute("type","text/javascript")
  fileref.setAttribute("src", filename)
 }
 else if (filetype=="css"){ //if filename is an external CSS file
  var fileref=document.createElement("link")
  fileref.setAttribute("rel", "stylesheet")
  fileref.setAttribute("type", "text/css")
  fileref.setAttribute("href", filename)
 }
 if (typeof fileref!="undefined")
  document.getElementsByTagName("head")[0].appendChild(fileref)
}

%for p in css:
  loadjscssfile('/static/'+'{{p}}', 'css');
%end

%for p in js:
  loadjscssfile('/static/'+'{{p}}', 'js');
%end

</script>




%helper = app.helper

%collapsed_s = ''
%collapsed_j = 'false'
%if collapsed:
   %collapsed_s = 'collapsed'
   %collapsed_j = 'true'
%end


<script type="text/javascript">
$(document).ready(function(){

  var w = {'id' : '{{wid}}', 'base_url' : '{{base_url}}', 'collapsed' : {{collapsed_j}}, 'position' : 'widget-place-1',
          'options' : {'key' : 'value'}};


  %for (k, v) in options.iteritems():
     %value = v.get('value', '')
     w.options['{{k}}'] = '{{value}}';
  %end

  // save into widgets
  widgets.push(w);


});

  function submit_{{wid}}_form(){
    var form = document.forms["options-{{wid}}"];
    console.log('Saving form'+form+'and widget'+'{{wid}}');
    var widget = find_widget('{{wid}}');
    // If we can't find the widget, bail out
    if(widget == -1){console.log('cannot find the widget for saving options!'); return;}
    console.log('We fond the widget'+widget);
    %for (k, v) in options.iteritems():
       %# """ for checkbox, the 'value' is useless, we must look at checked """
       %if v.get('type', 'text') == 'bool':
          var v = form.{{k}}.checked;
       %else:
          var v = form.{{k}}.value;
       %end
       console.log('Saving the {{k}} with the value'+v);
       widget.options['{{k}}'] = v;
    %end
    // so now we can ask for saving the state :)
    ask_for_widgets_state_save();
  }


</script>



<div class="widget movable collapsable removable editable closeconfirm {{collapsed_s}}" id="{{wid}}">
  <div class="widget-header">
    <strong>{{title}}</strong>
  </div>
  <div class="widget-editbox">
    <form name='options-{{wid}}' class="well">
      %for (k, v) in options.iteritems():
         %value = v.get('value', '')
         %label = v.get('label', k)
         %t = v.get('type', 'text')
         %if t != 'hidden':
           <label></label>
           <span class="help-inline">{{label}}</span>
	 %end
	 
	 %# """ Manage the differents types of values"""
         %if t in ['text', 'int']:
            <input name='{{k}}' value='{{value}}'/>
	 %end
	 %if t == 'hidden':
	    <input type="hidden" name='{{k}}' value='{{value}}'/>
	 %end
	 %if t in ['select']:
	    %values = v.get('values', [])
	    <select name='{{k}}'>
	      %for sub_val in values:
	         <option value="{{sub_val}}">{{sub_val}}</option>
	      %end
            </select>
	 %end
	 %if t == 'bool':
	    %checked = ''
	    %if value:
	       %checked = 'checked'
	    %end
	    <input name='{{k}}' type="checkbox" {{checked}}/>
	 %end

      %end
  
     <label></label>
     <a class="widget-close-editbox btn btn-success" onclick="submit_{{wid}}_form();" title="Save changes"><i class="icon-search"></i> Save changes</a>

    </form>

  </div>
  <div class="widget-content">
    
    %include

  </div>
</div>

