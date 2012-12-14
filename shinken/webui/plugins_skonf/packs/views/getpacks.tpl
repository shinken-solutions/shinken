%rebase layout_skonf globals(), js=['packs/js/packs.js', 'packs/js/getpack.js'], css=['packs/css/tags.css'], title='Get packs'

<script TYPE="text/javascript">
function submit() {
  document.forms['getpacks'].submit();
}
</script>

<div class="row-fluid">
  <div class="span12">
    <h1>Get new packs</h1>
    <div class="row-fluid">
      <div class="span9">
        %if error:
        <div class="alert alert-error"> {{error}}</div>
        %end

        %if api_error:
        <div id="warn-pref" class="hero-unit hero-unit-small alert-critical">
          <!-- <div class="span1" style="font-size: 50px; padding-top: 10px;"> <i class="icon-bolt font-white"></i> </div> -->
          <p>Oups! There was a problem with the API server connection</p>
          <p id="api_error" class="hide">{{api_error}}</p>
          <p>
              <a href="javascript:$('#api_error').show()" class='btn btn-warning'> <i class="icon-remove"></i> Show the error</a>
              <a href='/testapi' class='btn btn-success'> <i class="icon-upload"></i> Try an API server connection</a>
          </p>
        </div>
        %end
        <div id="message" class='alert span5 offset2 hide'> </div>

        %if search:
        <h3> Search for {{search}}</h3>
        <div class="span12">
          %if len(results) == 0:
          No results found
          %else:
          %for p in results:
          %pid = p.get('_id')
          %inst_lnk = p.get('install','')
          <div class="well">
            <!-- {{p}} -->
            <span class='label'>
              %src = p.get('img', '')
              <img class="imgsize3" onerror="$(this).hide()" src="{{src}}"/> {{p.get('pack_name', 'unknown')}}
            </span>
            <span>Provide host tags:
              <ul>
                %for t in p.get('templates', []):
                <li>{{t}}</li>
                %end
              </ul>
            </span>
            <span>Description: {{p.get('description', '')}}
            </span>
            <span id='loading-{{pid}}' class='pull-right hide'>
              <img src='/static/images/spinner.gif'>
            </span>
            <span class='pull-right'>
              <a id='download-{{pid}}' href='javascript:download_pack("{{inst_lnk}}", "{{pid}}");' class='btn btn-success' data-complete-text="Done!" data-loading-text="Loading.." > Install it!</a>
            </span>
            <span id="message-{{pid}}" class='span10 alert hide'>
            </span>
          </div>
          %end
          %end
        </div>
        %end
      </div>

      <div class="span3">
        <form class="form-search" name="getpacks" action="/getpacks" METHOD="POST">
          <div class="input-prepend">
            <span class="add-on"> <i class="icon-search"></i> </span>
            <input type="text" name='search' class="span10" placeholder="Search">
          </div>
          <button href="javascript:submit();" class="btn span4 pull-right"> Search</button>
        </form>

        %if categories:
        <div id="categories" class="well well-small">
          <h4>All categories</h4>
          {{!print_cat_tree(categories)}}
        </div>
        %end 

        %if tags:
        <div id="tagCloud" class="well well-small">
          <ul id="tagList">
            %nb_tags = len(tags)
            %i = 0
            %for t in tags:
            %name = t['name']
            %size = t['size']
            %occ = t['occ']
            <li> <a href='/getpacks/{{name}}' style='font-size:{{size}}em;'>{{name}} ({{occ}})</a> </li>
            %end
          </ul>
        </div>
        %end
      </div>
    </div>
  </div>
</div>