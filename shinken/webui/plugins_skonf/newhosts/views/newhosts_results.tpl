
%rebase layout_skonf globals()

<div> <h1> Discover your new hosts </h1> </div>

<p>Here are the scans :</p>
%for s in scans:
     <br/>{{s}}
%end

<p>Here are the results :</p>

%for h in pending_hosts:
     <br/>{{h}}
     <form method="get" id="host-{{h['host_name']}}" action="/add">
       <span class="table">
	 <span class="row">
	   <span class="cell">
	     <input name="tags" type="text" tabindex="1" value="{{h['use']}}" id="use-{{h['host_name']}}"/>
	   </span>
	   <span class="cell">
	     <a tabindex="4" href="javascript: submitform()">
	       <img src="/static/images/search.png" alt="search"/>
	     </a>
	   </span>
	 </span>
       </span>
     </form>

     %# " Add the auto copleter in the search input form"
     <script type="text/javascript">
       document.addEvent('domready', function() {
         var tags = $("use-{{h['host_name']}}");
 
         // Our instance for the element with id "use-"
         new Autocompleter.Request.JSON(tags, '/lookup/tag', {
            'indicatorClass': 'autocompleter-loading',
            'minLength': 3,
            'multiple': true,
         });
       
       });
     </script>


%end
