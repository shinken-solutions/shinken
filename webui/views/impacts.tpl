

%include header js=['check_mk.js', 'hover.js'], title='All critical impacts for your business', css=['check_mk.css']




    <div class="whole-page">
      <div>
	<h1 id="branding">
	  <a class="header_link">Shinken UI (inspired by Meatball)</a>
	</h1>
      </div>
      
      <div class="placemainmenu">
	<ul id="mainmenu" class="twoLevelMenu">
	  
	  <li class=""><a href="#" target="_blank">Dashboard</a>
	    
	  </li>

	  <li class=""><a href="#">Host</a>
	    <ul style="display: none; ">
	      <li><a href="#">Quick Overview</a></li>
	    </ul>
	  </li>
	  
	  <li class=""><a href="#">Services</a>
	    <ul style="display: none; ">
	      <li><a href="#">Quick Overview</a></li>
	    </ul>
	  </li>
	  
	  <li class="active"><a href="#">Incidents</a>
	    <ul style="display: block; ">
	      <li><a href="#">Business Impacts</a></li>
	      <li><a href="#">IT problems</a></li>
	    </ul>
	  </li>
	  <li><a href="">System</a>
	    <ul>
	      <li><a href="#">System Info</a></li>
	      <li><a href="#">Performance Info</a></li>
	    </ul>
	  </li>
	  
	</ul>
      </div>
      
      

      <div>
	<h4 id="page-heading">Incidents &gt;&gt; Business impacts</h4>
      </div>
      
      

      <div class="impacts-panel" style="min-height: 983px; ">

%for imp_id in impacts:
%   impact = impacts[imp_id]

	<div class="impact pblink" id="{{imp_id}}">
	  <div class="show-problem" id="show-problem-{{imp_id}}">
	    <img src="static/images/trig_right.png" id="show-problem-img-{{imp_id}}">
	  </div>
	  %for i in range(2, impact['criticity']):
	    <div class="criticity-icon-{{i-1}}">
	      <img src="static/images/star.png">
	    </div>
	  %end


	  <div class="impact-icon"><img src="static/images/50x50.png"></div>
	  <div class="impact-row"><span class="impact-name">{{impact['name']}}</span> is <span class="impact-state-text">{{impact['status']}}</span><img src="static/images/bomb.png"></div>
	  <div class="impact-row"><span class="impact-output">No mails can be send nor received</span></div>
	  <div class="impact-row"><span class="impact-duration">since one hour</span></div>
	</div>
%# end of the for imp_id in impacts:
%end

      </div>
      
      <div class="right-panel"><h3>This view was generated from CheckMK multisite backend. You can get this application <a href='http://mathias-kettner.de/checkmk_multisite.html'> here </a></h3>

      </div><script language="JavaScript"> var all_ids = new Array('3','2','1')</script>


      

%########    Now we will output righ panel with all root problems
      <div class="problems-panels">

%for imp_id in impacts:
%   impact = impacts[imp_id]




	<div class="problems-panel" id="problems-{{imp_id}}" style="visibility: hidden; zoom: 1; opacity: 0; ">
	  <div class="right-panel-top"> 
	    <div class="pblink" id="{{imp_id}}"> Close </div>
	  </div><br style="clear: both">
	  <div class="impact-icon-big"><img src="static/images/80x80.png">
	  </div>
	  <center>
	    <div class="impact-row"><span class="impact-name">{{impact['name']}}</span> is <span class="impact-state-text">{{impact['status']}}</span>
	    </div>
	  </center>
	  <br style="clear: both">
	  Root problems unamanaged :

	  %for pb_id in impact['problems']:
	  %   pb = problems[pb_id]
	  <div class="problem" id="{{pb_id}}">
	    <div class="divhstate1">{{pb['name']}}</div>
	    <div class="problem-actions" id="actions-pb_id">
	      <div class="action-fixit" id="fixit/paris/router-us"><img class="icon" title="Try to fix it" src="static/images/icon_ack.gif">Try to fix it</div> 
	      <div class="action-ack" id="ack/paris/router-us"><img class="icon" title="Acknoledge it" src="static/images/link_processes.gif">Acknoledge it</div>
	    </div>
	  </div>
	  %# end for pb_id in impacts['problems']:
	  %end
	  
	</div>
%# end for imp_id in impacts:
%end




      </div>
    </div>
    
    <table class="footer"><tbody><tr><td class="left"></td><td class="middle"></td><td class="right"></td></tr></tbody>
    </table>

%include footer
    
