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
          <li><a href="#">Dashboard</a></li>
          <li class="active"><a href="#">Shinken UI</a></li>
          <li><a href="#">Skonf UI</a></li>
          %end
        </ul>
        
        %if user is not None:
        <div class="nav-controll"> 
          <ul class="nav pull-right"> 
            <li class="divider-vertical"></li>
            <li><a href="/user/logout"><i class="icon-settings"></i></a></li>
            <li><a href="/user/logout"><i class="icon-logout"></i></a></li>
          </ul>           
          <div class="pull-right"> 
            <p class="navbar-text"><span id="greeting"></span> <span><a href="#"> Dummy<!-- {{user}} --></a></span>!</p> 
          </div> 
        </div>
        <!--<form class="navbar-search pull-right">
          <input type="text" class="search-query" placeholder="Search">
        </form>-->
        %end
      </div><!--/.nav-collapse -->
    </div>
  </div>
</div>
