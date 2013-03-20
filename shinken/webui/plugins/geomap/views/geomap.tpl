
<script type="text/javascript" src="http://maps.google.com/maps/api/js?sensor=false"></script>
<script type="text/javascript" src="https://raw.github.com/padolsey/jQuery-Plugins/master/sortElements/jquery.sortElements.js"></script>
<script type="text/javascript" src="https://raw.github.com/kaktus621/google-maps-api-addons/master/daynightoverlay/src/daynightoverlay.min.js"></script>
<script type="text/javascript" src="http://google-maps-utility-library-v3.googlecode.com/svn/trunk/markerclustererplus/src/markerclusterer.js"></script>
<script type="text/javascript" src="http://google-maps-utility-library-v3.googlecode.com/svn/trunk/markerwithlabel/src/markerwithlabel.js"></script>



%rebase layout globals(), js=['geomap/js/geomap.js'], css=['geomap/css/geomap.css']



<div id="alertsmap" class='span8' ></div>
<div id="alertsdetails">
  <table id="hostsalerts" class="alerts">
    <thead>
      <tr>
	<th class="sort">Sort</th>
	<th>Host</th>
	<th>Duration</th>
      </tr>
    </thead>
    <tbody>
    </tbody>
  </table>

  <table id="servicesalerts" class="alerts">
    <thead>
      <tr>
	<th class="sort">Sort</th>
	<th style="width: 15%">Host</th>
	<th style="width: 15%">Duration</th>
	<th style="width: 25%">Service</th>
	<th>Output</th>
      </tr>
    </thead>
    <tbody>
    </tbody>
  </table>
</div>
<div id="commentsdiv">
  <table id="comments" class="comments">
    <thead>
      <tr>
	<th class="sort">Sort</th>
	<th style="width: 15%">Date</th>
	<th style="width: 15%">Host</th>
	<th style="width: 15%">Service</th>
	<th style="width: 15%">Author</th>
	<th>Comment</th>
      </tr>
    </thead>
    <tbody>
    </tbody>
  </table>
</div>
