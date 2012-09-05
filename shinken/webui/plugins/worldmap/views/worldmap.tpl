
%rebase layout globals()

<script type="text/javascript" src="http://maps.google.com/maps/api/js?sensor=false"></script>

<style type="text/css">
  .map_container{position:relative;width:990px;margin:auto;background:#FFFFFF;padding:20px 0px 20px 0px;}
  .map_container h1{margin:0px 0px 10px 20px;}
  .map_container p{margin:10px 0px 10px 20px;}
  .map_container #map{width:700px;height:500px;margin:auto;}
</style>


<div class="map_container">
  <h1>World map about your servers</h1>
  <div id="map">
    <p>Map loading</p>
  </div>
</div>



<!-- Here we are initialysing the camera position. We place it in the first element, or 0,0 -->
%camera = (0, 0)
%for h in hosts:
  %camera = (float(h.customs.get('_LAT')), float(h.customs.get('_LONG')))
%end


<script>
  var map;

  initialize = function(){
     var latHome = new google.maps.LatLng({{camera[0]}}, {{camera[1]}});
     var myOptions = {
        zoom      : 14,
        center    : latHome,
        mapTypeId : google.maps.MapTypeId.TERRAIN, // Choose between HYBRID, ROADMAP, SATELLITE, TERRAIN
        maxZoom   : 20
     };

     map      = new google.maps.Map(document.getElementById('map'), myOptions);

  <!-- We are putting a mark on all valid hosts -->
  %for h in hosts:
    var lat_host = new google.maps.LatLng( {{float(h.customs.get('_LAT'))}} , {{float(h.customs.get('_LONG'))}} )
    var marker = new google.maps.Marker({
      position : lat_host,
      map      : map,
      title    : '{{h.get_name()}}'
    });

    var contentMarker = [
        '<div class="row" id="innermap-"{{app.helper.get_html_id(h)}}>',
        '<img class="span1" style="width: 48px;height: 48px;" src="{{app.helper.get_icon_state(h)}}" />',
        '<h3 class="span8"> The host {{h.get_name()}} is {{h.state}}.</h3><p>',
        '</div>'
    ].join('');

    var infoWindow = new google.maps.InfoWindow({
      content  : contentMarker,
      position : lat_host
    });

    google.maps.event.addListener(marker, 'click', function() {
      infoWindow.open(map, marker);
    });
  %end
  };


  <!-- Ok go initialize the map with all elements when it's loaded -->
  $(document).ready(initialize);

</script>
