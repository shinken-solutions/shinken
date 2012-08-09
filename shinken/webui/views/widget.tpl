%# Load all css stuff we need
%if not 'css' in locals(): css = []
%if not 'js' in locals(): js = []

<script type="text/javascript">
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
        var w = {'id': '{{wid}}', 'base_url': '{{base_url}}', 'collapsed': {{collapsed_j}}, 'position': 'widget-place-1',
                'options': {'key': 'value'}};

        %for (k, v) in options.iteritems():
             %value = v.get('value', '')
             w.options['{{k}}'] = '{{value}}';
        %end

        // save into widgets
        widgets.push(w);
        if( new_widget) {
            new_widget = false;
            saveWidgets();
        }
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
        saveWidgets();
        // Reloading the dashboard to let users see the changes.
        // Would be better to only reload the widget...
        window.location=window.location;
        // Prevent the form to be actually sent.
        return false;
    }
</script>

%editable = 'editable'
%if len(options) == 0:
  %editable = ''
%end

<div class="widget movable collapsable removable {{editable}} closeconfirm {{collapsed_s}}" id="{{wid}}">
  <div class="widget-header">
    <strong>{{title}}</strong>
  </div>
  <div class="widget-editbox">
    <form name="options-{{wid}}" class="well" onsubmit="return submit_{{wid}}_form();">
      %for (k, v) in options.iteritems():
        %value = v.get('value', '')
        %label = v.get('label', k)
        %t = v.get('type', 'text')
        %if t != 'hidden':
          <label></label>
          <span class="help-inline">{{label}}</span>
        %end

        %# """ Manage the differents types of values"""
        %if t in ['text', 'int', 'hst_srv']:
          <input name='{{k}}' value='{{value}}' id='input-{{wid}}-{{k}}'/>
          %if t == 'hst_srv':
            <script>link_elt_typeahead('input-{{wid}}-{{k}}');</script>
          %end
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
      <a class="widget-close-editbox btn btn-success" onclick="return submit_{{wid}}_form();" title="Save changes"><i class="icon-search icon-white"></i> Save changes</a>

    </form>

  </div>
  <div class="widget-content">
    %include
  </div>
</div>

