%import time
%now = time.time()
%helper = app.helper
%datamgr = app.datamgr

%rebase widget globals(), css=['graphs/css/widget_graphs.css']

%if not elt:
    <span>No element selected!</span>
%else:

  <!-- Reduce the time range of the dashboard graph. Last hour.
   and specify the source  : dashboard !-->
  %uris = app.get_graph_uris(elt, now - 3600, now, 'dashboard')
  %if len(uris) == 0:
    <span>No graph for this element</span>
  %end


    %for g in uris:
      %img_src = g['img_src']
      %link = g['link']
     <p class='widget_graph'>
       <a href="{{link}}" target='_blank'><img src="{{img_src}}"></a>
     </p>

   %end


%end


