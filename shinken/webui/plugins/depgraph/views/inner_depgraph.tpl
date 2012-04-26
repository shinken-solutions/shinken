%helper = app.helper
%datamgr = app.datamgr
%import time

%# If got no Element, bailout
%if not elt:
Invalid element
%else:



<script type="text/javascript">
  var depgraph_width = 400;
  var depgraph_height = 400;
  var depgraph_injectInto = 'infovis-'+'{{helper.get_html_id(elt)}}';

  loadjscssfile('/static/depgraph/css/eltdeps_widget.css', 'css');
  loadjscssfile('/static/depgraph/css/eltdeps.css', 'css');
  loadjscssfile('/static/depgraph/js/jit-yc.js', 'js');
  loadjscssfile('/static/depgraph/js/excanvas.js', 'js');
  loadjscssfile('/static/depgraph/js/eltdeps.js', 'js');
  

%# rebase widget globals(), title='Dependencies graph of ' + elt.get_full_name(),  js=['depgraph/js/jit-yc.js', 'depgraph/js/excanvas.js', 'depgraph/js/eltdeps.js'],  css=['depgraph/css/eltdeps.css', 'depgraph/css/eltdeps_widget.css'],  print_menu=False

  var graph_root = '{{elt.get_full_name()}}';
  var json_graph = {{!helper.create_json_dep_graph(elt, levels=4)}};

</script>



<div id="inner-details"></div>
<div id="infovis-{{helper.get_html_id(elt)}}"> </div>

<div id="log">Loading element informations...</div>


%#End of the Host Exist or not case
%end



