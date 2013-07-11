%if 'app' not in locals(): app = None

<script type="text/javascript">
  function webui() {
      var Port = {{app.get_webui_port()}}
      var Host = document.domain;
      var Url = 'http://' + Host + ':' + Port;
      return Url;
  }

  $(function(){
      $("a[href=':7767']").attr('href', webui());
  });
</script>

<div class="navbar navbar-fixed-top">
  <div class="navbar-inner">
    <div class="container-fluid">
      <a class="btn btn-navbar" data-toggle="collapse" data-target=".nav-collapse">
        <span class="i-bar"></span>
        <span class="i-bar"></span>
        <span class="i-bar"></span>
      </a>

      <div class="nav-collapse">
       <ul class="nav">
         <li class="dropdown">
           <a href="#" class="dropdown-toggle brand" data-toggle="dropdown" style="color: #FFFFFF"> Shinken <b class="caret"></b></a>
           <ul class="dropdown-menu">
            <li><a href=":7767">Shinken UI </a></li>
            <!-- We will add also others UIs on the global menu -->
            %if app:
            %other_uis = app.get_external_ui_link()
            <!-- If we add others UIs, we separate them from the inner ones-->
            %if len(other_uis) > 0:
            <li class="divider"></li>
            %end
            %for c in other_uis:
            <li><a href="{{c['uri']}}">{{c['label']}}</a></li>
            %end
            %end
          </ul>
        </li>
      </ul>

      <ul class="nav">
        %menu = [ ('/dashboard', 'Dashboard'), ('/impacts','Impacts'), ('/problems','IT problems'), ('/all', 'All'), ('/wall', 'Wall')]
        %for (key, value) in menu:
        %# Check for the selected element, if there is one
        %if menu_part == key:
        <li class="active"><a href="{{key}}">{{value}}</a></li>
        %else:
        <li><a href="{{key}}">{{value}}</a></li>
        %end
        %end
      </ul>

     <ul class="nav">
      <li class="dropdown">
        <a href="#" class="dropdown-toggle" data-toggle="dropdown"> System <b class="caret"></b></a>
        <ul class="dropdown-menu">
          <li><a href="/system">Shinken state</a></li>
          <!-- Comment until the page is done <li><a href="/system/log">System logs</a></li> -->
        </ul>
      </li>
    </ul>

    %if user is not None:
    <div class="nav-controll">
      <ul class="nav pull-right">
        <li class="divider-vertical"></li>
        %# Check for the selected element, if there is one
        %if menu_part == '/dashboard':
        <li><a class="quickinfo" data-original-title='Currently' href="/dashboard/currently"><i class="nav-icon icon-fullscreen"></i></a></li>
        %else:
        <li></li>
        %end

        %if app:
        %overall_itproblem = app.datamgr.get_overall_it_state()
        %if overall_itproblem == 0:
        <li><a href="/problems" class="quickinfo" data-original-title='IT Problems'><i class="icon-itproblem"></i><span class="pulsate badger badger-ok">OK!</span> </a></li>
        %elif overall_itproblem == 1:
        <li><a href="/problems" class="quickinfo" data-original-title='IT Problems'><i class="icon-itproblem"></i><span class="pulsate badger badger-warning">{{app.datamgr.get_nb_all_problems(app.get_user_auth())}}</span> </a></li>
        %elif overall_itproblem == 2:
        <li><a href="/problems" class="quickinfo" data-original-title='IT Problems'><i class="icon-itproblem"></i><span class="pulsate badger badger-critical">{{app.datamgr.get_nb_all_problems(app.get_user_auth())}}</span> </a></li>
        %end
        %end

        %if app:
        %overall_state = app.datamgr.get_overall_state()
        %if overall_state == 2:
        <li><a href="/impacts" class="quickinfo" data-original-title='Impacts'><i class="icon-impact"></i><span class="pulsate badger badger-critical">{{app.datamgr.get_len_overall_state()}}</span> </a></li>
        %elif overall_state == 1:
        <li><a href="/impacts" class="quickinfo" data-original-title='Impacts'><i class="icon-impact"></i><span class="pulsate badger badger-warning">{{app.datamgr.get_len_overall_state()}}</span> </a></li>
        %end
        %end
        <!-- <li><a href="#" class="quickinfo" data-original-title='Settings'><i class="icon-setting"></i></a></li>-->
        <!-- <li><a href="/user/logout" class="quickinfo" data-original-title='Logout'><i class="nav-icon icon-off"></i></a></li> -->
        <ul class="nav pull-right">
          <li class="dropdown">
            <a href="#" class="dropdown-toggle" data-toggle="dropdown">Hi {{user.get_name().capitalize()}} <b class="caret"></b></a>
            <ul class="dropdown-menu">
              <li> <a class="disabled-link" href="#"><i class="icon-pencil"></i> Edit profile</a> </li>
	      <li> <a class="" href="http://www.shinken-monitoring.org/wiki/"><i class="icon-external-link"></i> Help</a></li>
              <li class="divider"></li>
              <li> <a href="/user/logout" data-original-title='Logout'><i class="icon-off"></i> Logout</a></li>
            </ul>
          </li>
        </ul>
      </ul>
    </div>

    <script>  
      $(function ()  
      { $("#searchhelp").popover({trigger: 'click', placement:'bottom', html: 'true', animation: 'true'});  
      });  
    </script> 

    <form name="global_search" class="navbar-search pull-right topmmargin1" action='#'>
      <input type="text" class="search-query typeahead no-bottommargin" autocomplete="off" placeholder="Search" name="global_search">
      <a id="searchhelp" href="http://www.shinken-monitoring.org/wiki/webui_search" target="_blank"><i class="icon-question-sign font-white topmmargin2"></i></a>  
    </form>
    %end
  </div><!--/.nav-collapse -->
</div>
</div>
</div>
