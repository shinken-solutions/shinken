

%print 'Elt value?', elt
%import time

%# If got no Element, bailout
%if not elt:
%rebase widget title='Invalid element name'

Invalid element

%else:

%helper = app.helper
%datamgr = app.datamgr


<script type="text/javascript">
  var depgraph_width = 400;
  var depgraph_height = 400;
  var depgraph_injectInto = 'infovis-'+'{{helper.get_html_id(elt)}}';
</script>


%rebase widget globals(), title='Dependencies graph of ' + elt.get_full_name(),  js=['depgraph/js/jit-yc.js', 'depgraph/js/excanvas.js', 'depgraph/js/eltdeps.js'],  css=['depgraph/css/eltdeps.css', 'depgraph/css/eltdeps_widget.css'],  print_menu=False



<script src=/static/depgraph/js/eltdeps.js></script>
<script type="text/javascript">
  
  // var graph_root = '{{elt.get_full_name()}}';
  // var json_graph = {{!helper.create_json_dep_graph(elt, levels=4)}};
  //console.log('Show the graph'+json_graph);
 
 
 $(document).ready(init_graph('{{elt.get_full_name()}}', {{!helper.create_json_dep_graph(elt, levels=4)}},400, 400,'{{helper.get_html_id(elt)}}'));
 
 
</script>




<div id="right-container" class="border">
  <div id="inner-details-{{helper.get_html_id(elt)}}">
</div>
  
</div>

<div id="infovis-{{helper.get_html_id(elt)}}"> </div>

  <div id="log">Loading element informations...</div>
</div>
  
<div class="clear"></div>
</div>

%#End of the Host Exist or not case
%end



