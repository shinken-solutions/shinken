
%rebase layout globals()


<style type="text/css">
  .map_container{position:relative;width:990px;margin:auto;background:#FFFFFF;padding:20px 0px 20px 0px;}
  .map_container h1{margin:0px 0px 10px 20px;}
  .map_container p{margin:10px 0px 10px 20px;}
  .map_container #map{width:700px;height:500px;margin:auto;}
</style>


<div class="map_container">
  <h1>Test MAP</h1>
  <div id="map">
    <p>Map loading</p>
  </div>
</div>
<script type="text/javascript" src="http://maps.google.com/maps/api/js?sensor=false"></script>

<script>
var map;
var initialize;

initialize = function(){
   var latHome = new google.maps.LatLng(44.5378, -0.600); // Near my home :)
  var myOptions = {
    zoom      : 14,
    center    : latHome,
    mapTypeId : google.maps.MapTypeId.TERRAIN, // Choose between HYBRID, ROADMAP, SATELLITE, TERRAIN
    maxZoom   : 20
  };

  map      = new google.maps.Map(document.getElementById('map'), myOptions);

  var marker = new google.maps.Marker({
    position : latHome,
    map      : map,
    title    : "Home"
  });

  var contentMarker = [
      '<div id="innermap">',
       "<h3>It's my home!</h3><p>",
      '</div>'
  ].join('');

  var infoWindow = new google.maps.InfoWindow({
    content  : contentMarker,
    position : latHome
  });

  google.maps.event.addListener(marker, 'click', function() {
    infoWindow.open(map, marker);
  });

};

initialize();
</script>
