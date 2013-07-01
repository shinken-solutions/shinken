%if 'app' not in locals(): app = None


	<div data-role="page" id="home2" data-theme="a">
        <div data-role="header" data-backbtn="true" data-position="fixed">
                <h1>Shinken
                </h1>
                %if locals()['print_menu'] == True:
                	%if locals()['back_hide'] == False:
	                	<a href="#" data-icon="back" data-rel="back" data-transition="slideleft" class="ui-btn-left">Back</a>
					%end

	               	<a href="/mobile/main" data-icon="home" data-transition="slidedown" data-iconpos="notext" class="ui-btn-right">Home</a>

                	%# Menu composition
                	%if menu_part <> '':
		                <div data-role="navbar">
		                        <ul>
		                        	%if menu_part == '/dashboard':
		                        		<li><a id="left_link" data-direction="reverse" href="/mobile/system" data-transition="slide">System state</a></li>
		                                <li><a href="/mobile/dashboard" data-transition="slide" class="ui-btn-active">Dashboard</a></li>
		                                <li><a id="right_link" href="/mobile/problems" data-transition="slide">Problems</a></li>
		                        	%elif menu_part == '/problems':
		                        		<li><a id="left_link" data-direction="reverse" href="/mobile/dashboard" data-transition="slide">Dashboard</a></li>
		                                <li><a href="/mobile/problems" data-transition="slide" class="ui-btn-active">Problems</a></li>
		                                <li><a id="right_link" href="/mobile/impacts" data-transition="slide">Impacts</a></li>
		                        	%elif menu_part == '/impacts':
		                        		<li><a id="left_link" data-direction="reverse" href="/mobile/problems" data-transition="slide">Problems</a></li>
		                                <li><a href="/mobile/impacts" data-transition="slide" class="ui-btn-active">Impacts</a></li>
		                                <li><a id="right_link" href="/mobile/log" data-transition="slide">Log</a></li>
	                                %elif menu_part == '/log':
	                                	<li><a id="left_link" data-direction="reverse" href="/mobile/impacts" data-transition="slide">Impacts</a></li>
		                                <li><a href="/mobile/log" data-transition="slide" class="ui-btn-active">Log</a></li>
		                                <li><a id="right_link" href="/mobile/wall" data-transition="slide">Wall</a></li>
	                                %elif menu_part == '/wall':
	                                	<li><a id="left_link" data-direction="reverse" href="/mobile/log" data-transition="slide">Log</a></li>
		                                <li><a href="/mobile/log" data-transition="slide" class="ui-btn-active">Wall</a></li>
		                                <li><a id="right_link" href="/mobile/system" data-transition="slide">System state</a></li>
	                                %elif menu_part == '/system':
	                                	<li><a id="left_link" data-direction="reverse" href="/mobile/wall" data-transition="slide">Wall</a></li>
		                                <li><a href="/mobile/system" data-transition="slide" class="ui-btn-active">System state</a></li>
		                                <li><a id="right_link" href="/mobile/dashboard" data-transition="slide">Dashboard</a></li>
	                                %end
		                        </ul>
		                </div>
	                %end
                %end
        </div>
