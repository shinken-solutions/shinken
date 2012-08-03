

%print 'Elt value?', elt
%import time

%# If got no Element, bailout
%if not elt:
%rebase layout title='Invalid element name'

Invalid element

%else:

%helper = app.helper
%datamgr = app.datamgr


%rebase layout globals(), title='Dependencies graph of ' + elt.get_full_name(),  refresh=True


<script src='/static/depgraph/js/eltdeps.js'></script>


<script type="text/javascript">
  loadjscssfile('/static/depgraph/css/eltdeps_widget.css', 'css');
  loadjscssfile('/static/depgraph/css/eltdeps.css', 'css');
  loadjscssfile('/static/depgraph/js/jit-yc.js', 'js');
  loadjscssfile('/static/depgraph/js/excanvas.js', 'js');


  // Now we hook teh global search thing
  $('.typeahead').typeahead({
    // note that "value" is the default setting for the property option
    source: function (typeahead, query) {
      $.ajax({url: "/lookup/"+query,
        success: function (data){
          typeahead.process(data)}
        });
      },
    onselect: function(obj) {
      $("ul.typeahead.dropdown-menu").find('li.active').data(obj);
    }
  });

  $(document).ready(init_graph('{{elt.get_full_name()}}', {{!helper.create_json_dep_graph(elt, levels=4)}}, 700, 700,'{{helper.get_html_id(elt)}}'));

</script>

<div id="right-container" class="border">
<div id="inner-details-{{helper.get_html_id(elt)}}"></div>
</div>
<div id="infovis-{{helper.get_html_id(elt)}}"> </div>

<div id="log">Loading element informations...</div>


<div class="clear"></div>


%#End of the Host Exist or not case
%end



