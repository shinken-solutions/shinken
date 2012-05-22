
%rebase layout_skonf globals(), js=['packs/js/packs.js']

<div> <h1> Get new packs </h1> </div>



<script TYPE="text/javascript">

function submit(){
   document.forms['getpacks'].submit();
}

</script>

%if error:
    <div class='alert alert-error span5 offset2'> {{error}}</div>
%end


<form class='well span5 offset2' name='getpacks' action='/getpacks' METHOD='POST'>
  <div class="input-prepend">
    <span class="add-on"><i class="icon-search"></i></span><input type="textarea" name='search' class="span4" placeholder="Search">
  </div>
  <a href='javascript:submit();' class='btn'> Search</a>
    
</form>


%if search:
<span class='span12'> <h3> Search for {{search}}</h3></span>
<div class='span10'>
  %if len(results) == 0:
  No results found
  %else:
    %for p in results:
      <div class='span8 well'>
	{{p}}
	<span class='label'>
	  %src = p.get('img', '')
	  <img class="imgsize3" onerror="$(this).hide()" src="{{src}}"/> {{p.get('pack_name', 'unknown')}}
	</span>
	<span>Provide host tags :
	  <ul>
	  %for t in p.get('templates', []):
	    <li>{{t}}</li>
	  %end
	  </ul>
	</span>
	<span>Description : {{p.get('description', '')}}
	</span>
	<span class='pull-right'>
	  <a href='{{p.get('install','')}}' class='btn btn-success'> Install it!</a>
	</span>
      </div>
    %end
  %end
</div>

%end

