%if 'app' not in locals(): app = None

<div class="navbar navbar-fixed-top">
  <div class="navbar-inner">
    <div class="container-fluid">
      <a class="btn btn-navbar" data-toggle="collapse" data-target=".nav-collapse">
        <span class="i-bar"></span>
        <span class="i-bar"></span>
        <span class="i-bar"></span>
      </a>
      <!--<a class="brand" href="#">Shinken</a>-->
      <div class="nav-collapse">
	<ul class="nav">
	  <li class="dropdown">
	    <a href="#" class="brand" style="color: #FFFFFF"> Shinken Packs</a>
	  </li>
	</ul>
	<ul class="nav">
	  <li><a href="/main">Home</a></li>
	</ul>

	<ul class="nav">
          <li><a href="/packs">Packs</a></li>
        </ul>


	<ul class="nav">
          <li><a href="/addpack">Upload a pack</a></li>
        </ul>


	%if not user : user = {}
	%print "USER IS", user
        %if True:
        <div class="nav-controll">
          <ul class="nav pull-right">
            <li class="divider-vertical"></li>

           <!-- <li><a href="#" class="quickinfo" data-original-title='Settings'><i class="icon-setting"></i></a></li>-->
            <li><a href="/user/logout" class="quickinfo" data-original-title='Logout'><i class="icon-logout"></i></a></li>
          </ul>

         </div>
	       <ul class="nav pull-right">
          <li class="dropdown">
            <a href="#" class="dropdown-toggle" data-toggle="dropdown">Hi {{user.get('username', 'unknown').capitalize()}} <b class="caret"></b></a>
	    %if user != {}:
	    %print "WTF?", user
            <ul class="dropdown-menu">
	      <a class='' href="/user/{{user.get('username', 'unknown')}}"><i class="icon-pencil"></i> My profile</a>
            </ul>
	    %else:
	    <ul class="dropdown-menu">
              <a class='' href="/register"><i class="icon-pencil"></i> Register</a>
              <a class='' href="/login"><i class="icon-pencil"></i> Login</a>
            </ul>

	    %end
          </li>
        </ul>

	<ul class="nav pull-right">
	  <li class="divider-vertical"></li>
	</ul>
        <form name='global_search' class="navbar-search pull-right" action='#'>
          <input type="text" class="search-query typeahead" autocomplete="off" placeholder="Search" name="global_search">
        </form>
        %end
      </div><!--/.nav-collapse -->
    </div>
  </div>
</div>

