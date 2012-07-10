

%print 'Elt value?', elt
%import time

%# If got no Element, bailout
%if not elt:
%rebase layout title='Invalid element name'

Invalid element

%# " If we got auth problem, we bail out"
%if not valid_user:
<script type="text/javascript">
  window.location.replace("/login");
</script>
%# " And if the javascript is not follow? not a problem, we gave no data here."
%end


%else:

%helper = app.helper
%datamgr = app.datamgr


<script type="text/javascript">
  var depgraph_width = 700;
  var depgraph_height = 700;
  var depgraph_injectInto = 'infovis';
</script>



%rebase layout globals(), title='Dependencies graph of ' + elt.get_full_name(),  js=['depgraph/js/jit-yc.js', 'depgraph/js/excanvas.js', 'depgraph/js/eltdeps.js'],  css=['depgraph/css/eltdeps.css'],  print_menu=False, refresh=True




<script type="text/javascript">
  var graph_root = '{{elt.get_full_name()}}';
  var json_graph = {{!helper.create_json_dep_graph(elt, levels=4)}};

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


</script>


<div id="infovis"> </div>
<div id="right-container" class="border">
%#  <div class="border"></div>
  <div id="inner-details"></div>
</div>

<div id="log">Loading element informations...</div>
</div>

<div class="clear"></div>
</div>

%#End of the Host Exist or not case
%end



