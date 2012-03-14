%if 'app' not in locals(): app = None

<div class="navbar navbar-fixed-top">
  <div class="navbar-inner">
    <div class="container-fluid">
      <a class="btn btn-navbar" data-toggle="collapse" data-target=".nav-collapse">
        <span class="i-bar"></span>
        <span class="i-bar"></span>
        <span class="i-bar"></span>
      </a>
      <a class="brand" href="#">Shinken</a>
      <div class="nav-collapse">
	<ul class="nav">
	  <li class="dropdown">
	    <a href="#" class="dropdown-toggle" data-toggle="dropdown"> UI <b class="caret"></b></a>
	    <ul class="dropdown-menu">
	      <li><a href="/dashboard">Dashboard</a></li>
              <li><a href="/">Shinken UI</a></li>
              <li><a href="/">Skonf UI</a></li>
	    </ul>
	  </li>
	</ul>
	
	<ul class="nav">
	  %menu = [ ('/', 'Dashboard'), ('/impacts','Impacts'), ('/problems','IT problems'), ('/all', 'All')]
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
              <li><a href="/system/log">System logs</a></li>
            </ul>
          </li>
        </ul>

	
        %if user is not None:
        <div class="nav-controll"> 
          <ul class="nav pull-right"> 
            <li class="divider-vertical"></li>
	    %if app:
	      %overall_state = app.datamgr.get_overall_state()
              %if overall_state == 2:
              <li><a href="#" class="quickinfo" data-original-title='Impacts'><i class="icon-impact"></i><span class="pulsate badger badger-critical">{{app.datamgr.get_len_overall_state()}}</span> </a></li>
              %elif overall_state == 1:
              <li><a href="#" class="quickinfo" data-original-title='Impacts'><i class="icon-impact"></i><span class="pulsate badger badger-warning">{{app.datamgr.get_len_overall_state()}}</span> </a></li>
              %end
	    %end
           <!-- <li><a href="#" class="quickinfo" data-original-title='Settings'><i class="icon-setting"></i></a></li>-->
            <li><a href="/user/logout" class="quickinfo" data-original-title='Logout'><i class="icon-logout"></i></a></li>
          </ul>           
          <div class="pull-right"> 
            <p class="navbar-text"><span id="greeting"></span> <span><a href="#"> Dummy<!-- {{user}} --></a></span>!</p> 
          </div> 
        </div>
	<ul class="nav pull-right">
	  <li class="divider-vertical"></li>
	</ul>
        <form class="navbar-search pull-right">
          <input type="text" class="search-query" placeholder="Search">
        </form>
        %end
      </div><!--/.nav-collapse -->
    </div>
  </div>
</div>
