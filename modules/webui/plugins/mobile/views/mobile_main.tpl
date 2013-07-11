%rebase layout_mobile globals(), title="Tactical view", js=['mobile/js/mobile_main.js'], css=['mobile/css/main.css'], menu_part='', back_hide=True

%overall_itproblem = app.datamgr.get_nb_all_problems(app.get_user_auth())

<div id="main" data-theme="a">

	<ul data-role="listview" data-inset="true" data-theme="a">
		<li><a href="/mobile/dashboard">Dashboard</a>
			<span class="ui-li-count ui-btn-up-c ui-btn-corner-all">{{len([pb for pb in problems if pb.state in ['DOWN', 'CRITICAL']])}} Critical</span>
		</li>
		%if overall_itproblem > 0:
			<li><a href="/mobile/problems">Problems<span class="ui-li-count ui-btn-up-c ui-btn-corner-all">{{app.datamgr.get_nb_all_problems(app.get_user_auth())}}</span></a></li>
			<li><a href="/mobile/impacts">Impact</a></li>
		%end
		<li><a href="/mobile/log">Log</a></li>
		<li><a href="/mobile/wall">Wall</a></li>
		<li><a href="/mobile/system">System state</a></li>
	</ul>
</div>
