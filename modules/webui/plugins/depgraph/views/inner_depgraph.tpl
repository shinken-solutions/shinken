%helper = app.helper
%datamgr = app.datamgr
%import time

%# If got no Element, bailout
%if not elt:
Invalid element
%else:


%# We need to sync load eltdeps.js and not in a asyncronous mode
<script src='/static/depgraph/js/eltdeps.js'></script>

<script type="text/javascript">
  loadjscssfile('/static/depgraph/css/eltdeps_widget.css', 'css');
  loadjscssfile('/static/depgraph/css/eltdeps.css', 'css');
  loadjscssfile('/static/depgraph/js/jit-yc.js', 'js');
  loadjscssfile('/static/depgraph/js/excanvas.js', 'js');


  $(document).ready(init_graph('{{elt.get_full_name()}}', {{!helper.create_json_dep_graph(elt, levels=4)}},400, 400,'{{helper.get_html_id(elt)}}'));

</script>



<div id="inner-details-{{helper.get_html_id(elt)}}"></div>
<div id="infovis-{{helper.get_html_id(elt)}}"> </div>

<div id="log">Loading element informations...</div>


%#End of the Host Exist or not case
%end



