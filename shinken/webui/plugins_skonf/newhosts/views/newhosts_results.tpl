
%rebase layout_skonf globals(), title="Discovery scan results", css=['newhosts/css/results.css', 'newhosts/css/token-input.css', 'newhosts/css/token-input-mac.css', 'newhosts/css/token-input-facebook.css'], js=['newhosts/js/results.js', 'newhosts/js/jquery.tokeninput.js']

<p>Here are the scans :</p>
%for s in scans:
     <br/>{{s}}
%end

<p>Here are the results :</p>

%for h in pending_hosts:
     %hname = h['host_name']
     <div id="host-{{h['host_name']}}" class="grid_10 discovered_host">
     <br/><!-- "{{h}}" -->
     <form method="post" id="form-{{h['host_name']}}" action="/newhosts/validatehost">
       <span class="table">
	 <span class="row">
	   <input name="_id" type="hidden" value="{{h['_id']}}"/>
	   <span class="cell">
             <label for="host_name">Hostname:</label>
             <input name="host_name" type="text" tabindex="1" value="{{h['host_name']}}" id="form-host_name-{{h['host_name']}}"/>
           </span>
	   <span class="cell">
	     <label for="tags">Tags:</label>
	     <input id='input-{{h['host_name']}}' class='to_use_complete' data-use='{{h['use']}}' name="tags" type="text" tabindex="2"  />
	   </span>
	   <span class="cell">
	     <a tabindex="4" href='javascript:validatehostform("{{h['host_name']}}")'>
	       <img class='form_button_image' src="/static/images/big_ack.png" alt="Validate"/>
	     </a>
	   </span>
	   <input type="submit" value="GO">
	   <div id="res-{{h['host_name']}}" class="log_result">
	     <h3>Ajax Response</h3>
	   </div>
	 </span>
       </span>
     </form>
     <a href='javascript:get_use_values("{{h['host_name']}}")'>TOTO</a>
     <div id="good-result-{{hname}}" class='div-result'>
       OK, the host {{hname}} was added succesfuly.
       <img class='form_button_image' src="/static/images/big_ack.png" alt="OK"/>
     </div>
     <div id="bad-result-{{hname}}" class='div-result'>
       ERROR : the host {{hname}} was not added succesfuly.
       <img class='form_button_image' src="/static/images/bomb.png" alt="Error"/>
     </div>


     </div>


%end



