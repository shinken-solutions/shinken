
%rebase layout_skonf globals(), title="Discovery scan results", css=['newhosts/css/results.css'], js=['newhosts/js/results.js']

<div> <h1> Discover your new hosts </h1> </div>

<p>Here are the scans :</p>
%for s in scans:
     <br/>{{s}}
%end

<p>Here are the results :</p>

%for h in pending_hosts:
     %hname = h['host_name']
     <div id="host-{{h['host_name']}}" class="grid_10 discovered_host">
     <br/>{{h}}
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
	     <input name="tags" type="text" tabindex="2" value="{{h['use']}}" id="form-use-{{h['host_name']}}"/>
	   </span>
	   <span class="cell">
	     <a tabindex="4" href='javascript: validatehostform("{{h['host_name']}}")'>
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

     <div id="good-result-{{hname}}" class='div-result'>
       OK, the host {{hname}} was added succesfuly.
       <img class='form_button_image' src="/static/images/big_ack.png" alt="OK"/>
     </div>
     <div id="bad-result-{{hname}}" class='div-result'>
       ERROR : the host {{hname}} was not added succesfuly.
       <img class='form_button_image' src="/static/images/bomb.png" alt="Error"/>
     </div>


     %# " Add the auto copleter in the search input form"
     <script type="text/javascript">
       document.addEvent('domready', function() {
         var tags = $("form-use-{{h['host_name']}}");
       
         // Our instance for the element with id "use-"
         new Autocompleter.Request.JSON(tags, '/lookup/tag', {
            'indicatorClass': 'autocompleter-loading',
            'minLength': 3,
            'multiple': true,
         });
       
       });
     </script>
     </div>


%end
