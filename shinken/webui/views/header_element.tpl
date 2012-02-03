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
              %if user is not None:
              <li class="active"><a href="#">Dashboard</a></li>
              <li><a href="#">Shinken UI</a></li>
              <li><a href="#">Sknonf UI</a></li>
              %end
            </ul>
            %if user is not None:
            <p class="navbar-text pull-right">Logged in as <a href="#"><!-- {{user}} --></a></p>
            <form class="navbar-search pull-right">
              <input type="text" class="search-query" placeholder="Search">
            </form>
            %end
          </div><!--/.nav-collapse -->
        </div>
      </div>
    </div>