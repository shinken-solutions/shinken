%if not 'app' in locals(): app = None
<div class="well sidebar-nav">
       <ul class="nav nav-list">
              <li class="nav-header">Monitor</li>

              %menu = [ ('/', 'Dashboard'), ('/impacts','Impacts'), ('/problems','IT problems'), ('/all', 'All') ]
              %for (key, value) in menu:

              %# Check for the selected element, if there is one
              %if menu_part == key:
                     <li><a href="{{key}}" id="active">{{value}}</a></li>
                     %else:
                     <li><a href="{{key}}">{{value}}</a></li>
                     %end
              %end

              <li class="nav-header">System</li>
              %menu = [ ('/system', 'System'), ('/system/log', 'Event Log') ]
              %for (key, value) in menu:

              %# Check for the selected element, if there is one
              %if menu_part == key:
                     <li><a href="{{key}}" id="active">{{value}}</a></li>
                     %else:
                     <li><a href="{{key}}">{{value}}</a></li>
                     %end
              %end
       </ul>
</div><!--/.well -->