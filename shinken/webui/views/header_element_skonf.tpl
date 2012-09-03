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
	    <a href="#" class="dropdown-toggle brand" data-toggle="dropdown" style="color: #FFFFFF"> Shinken <b class="caret"></b></a>
	    <ul class="dropdown-menu span4">
              <li><a href="/">Shinken UI </a></li>
              <li><a href="/">Skonf UI</a></li>
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
	<p style="color: red;">BETA</p>
	</ul>
	<ul class="nav">
	  <li><a href="/main">Home</a></li>
	</ul>

	<ul class="nav">
	  %if menu_part == '/newhosts':
          <li class="dropdown active">
	  %else:
	  <li class="dropdown">
	  %end
            <a href="#" class="dropdown-toggle" data-toggle="dropdown"> Discovery<b class="caret"></b></a>
            <ul class="dropdown-menu">
              <li><a href="/newhosts">Scan new hosts</a></li>
              <li><a href="/newhosts/results">Scan results</a></li>
            </ul>
          </li>
        </ul>


	<ul class="nav">
	  %if menu_part == '/elements':
          <li class="dropdown active">
	  %else:
	  <li class="dropdown">
	  %end
            <a href="#" class="dropdown-toggle" data-toggle="dropdown"> Objects<b class="caret"></b></a>
            <ul class="dropdown-menu">
	      %lst = ['hosts', 'services', 'contacts', 'commands', 'timeperiods']
	      %for i in lst:
                 <li><a href="/elements/{{i}}">{{i.capitalize()}}</a></li>
	      %end
            </ul>
          </li>
        </ul>


	<ul class="nav">
	  %if menu_part == '/packs':
          <li class="dropdown active">
	  %else:
	  <li class="dropdown">
	  %end
            <a href="#" class="dropdown-toggle" data-toggle="dropdown"> Packs<b class="caret"></b></a>
            <ul class="dropdown-menu">
	      <li><a href="/packs">Your packs</a></li>
	      <li><a href="/getpacks">Get new packs!</a></li>
            </ul>
          </li>
        </ul>



	<!-- Not finished from now
	     <ul class="nav">
	  %menu = [ ('/system','System'), ('/otheruis', 'Link with other UIs')]
          %for (key, value) in menu:
            %# Check for the selected element, if there is one
            %if menu_part == key:
              <li class="active"><a href="{{key}}">{{value}}</a></li>
            %else:
              <li><a href="{{key}}">{{value}}</a></li>
            %end
         %end
	</ul>
	     -->


        %if user is not None:
        <div class="nav-controll">
          <ul class="nav pull-right">
            <li class="divider-vertical"></li>

           <!-- <li><a href="#" class="quickinfo" data-original-title='Settings'><i class="icon-setting"></i></a></li>-->
            <li><a href="/user/logout" class="quickinfo" data-original-title='Logout'><i class="icon-logout"></i></a></li>
          </ul>

         </div>
	       <ul class="nav pull-right">
          <li class="dropdown">
            <a href="#" class="dropdown-toggle" data-toggle="dropdown">Hi {{user.get('contact_name', 'unknown').capitalize()}} <b class="caret"></b></a>
            <ul class="dropdown-menu">
	      <a class='' href="/elements/contacts/{{user.get('contact_name', 'unknown')}}"><i class="icon-pencil"></i> Edit profile</a>
            </ul>
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

