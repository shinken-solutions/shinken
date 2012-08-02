
<div data-role="footer" class="ui-bar" data-position="fixed" id="footer">
	<a href="#about" data-rel="dialog" data-role="button" data-icon="info" data-iconpos="notext" class="ui-btn-left">About</a>
	%if locals()['print_menu'] == True:
		<!--<a href="#" data-role="button" data-icon="search" data-iconpos="notext">Search</a>-->
		<div id="userFooter"><span class="username">{{user.get_name().capitalize()}}</span><a href="/user/logout" data-role="button" rel="external" data-icon="delete" data-iconpos="notext" class="ui-btn-right">Logout</a></div>
	%end
</div>
</div>
<!-- about =========================================================== -->
<div data-role="page" id="about" data-theme="a">
  <div data-role="header">
    <h1>About</h1>
  </div>

  <div data-role="content">
    <h2>Shinken v1.01</h2>
    <p>Shinken interface for iPhone, Android by Gaël, Maël, Julien, Damien, Hugo, Valentin</p>

    <dl>
      <dt>Project Home</dt>
      <dd><a href="http://www.shinken-monitoring.org/" rel="external">http://www.shinken-monitoring.org</a></dd>

      <dt>Github Repository</dt>
      <dd><a href="https://github.com/naparuba/shinken" rel="external">https://github.com/naparuba/shinken</a></dd>
    </dl>
  </div>
</div>
