
/*Copyright (C) 2009-2011 :
     Remi Buisson, remi.buisson87@gmail.com
     Gabes Jean, naparuba@gmail.com

 This file is part of Shinken.

 Shinken is free software: you can redistribute it and/or modify
 it under the terms of the GNU Affero General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Shinken is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Affero General Public License for more details.

 You should have received a copy of the GNU Affero General Public License
 along with Shinken.  If not, see <http://www.gnu.org/licenses/>.
*/




function durationToStr(dif) {
    // Constants
    var seconds = 1000;
    var minutes = seconds * 60;
    var hours = minutes * 60;
    var days = hours * 24;

    var difd = Math.floor(dif/days);
    var difh = Math.floor(dif/hours) - difd * 24;
    var difm = Math.floor(dif/minutes) - difd * 24 * 60 - difh * 60;
    var difs = Math.floor(dif/seconds) - difd * 24 * 3600 - difh * 3600 - difm * 60;
    
    var str = '';
    if (difd > 0) {
	str = difd + ' d ' + difh + ' h ' + difm + ' m ' + difs + ' s';
    }
    else if (difh > 0) {
	str = difh + ' h ' + difm + ' m ' + difs + ' s';
    }
    else if (difm > 0) {
	str = difm + ' m ' + difs + ' s';
    }
    else if (difs > 0) {
	str = difs + ' s';
    }

    return str;
}

function dateFormat(timestamp, format) {
    d = new Date(timestamp);

    str = format;
    str = str.replace('YYYY', d.getFullYear());
    str = str.replace('MM', ('0' + (d.getMonth() + 1)).slice(-2));
    str = str.replace('DD', ('0' + d.getDate()).slice(-2));
    str = str.replace('HH', ('0' + d.getHours()).slice(-2));
    str = str.replace('mm', ('0' + d.getMinutes()).slice(-2));
    str = str.replace('ss', ('0' + d.getSeconds()).slice(-2));

    return str;
}

function sortByStateAndDuration(table) {
    $('#' + table).find('td').filter(function(){
	return $(this).hasClass('sort');
    }).sortElements(function(a, b){
	level_a = parseInt($.text([a]).split('_')[0]);
	level_b = parseInt($.text([b]).split('_')[0]);

	duration_a = parseInt($.text([a]).split('_')[1]);
	duration_b = parseInt($.text([b]).split('_')[1]);

        if(level_a == level_b && duration_a <= duration_b)
            return 1;

	if(level_a > level_b)
            return 1;
	
        return -1;
    }, function(){
        return this.parentNode; 
	
    });
}

function sortByTime(table) {
    $('#' + table).find('td').filter(function(){
	return $(this).hasClass('sort');
    }).sortElements(function(a, b){
	a = parseInt($.text([a]));
	b = parseInt($.text([b]));

        if(a > b)
            return -1;
        return 1;
    }, function(){
        return this.parentNode; 
	
    });

}


function setBestSize(div) {
    var divheight = $('#' + div).height();
    var tableheight = 0;
    $.each($('#' + div).find('table'), function() {
	 tableheight += $(this).height();
    });

    if (tableheight > divheight) {
	$.each($('#' + div + ' table tr td:last-child'), function() {
	    $(this).css('overflow', 'hidden');
	    $(this).css('white-space', 'nowrap');
	    $(this).css('text-overflow', 'ellipsis');
	});
    }
    else {
	$.each($('#' + div + ' table tr td:last-child'), function() {
	    $(this).css('overflow', '');
	    $(this).css('white-space', '');
	    $(this).css('text-overflow', '');
	});
    }
}


function refreshMap() {
    var dc_icon = { url: 'images/datacenter.png',
		    scaledSize: new google.maps.Size(20, 32),
		  }

    var styles = [
	{
            url: '/static/img/icons/state_down.png',
	    height: 53,
            width: 52,
	}, 
	{
            url: '/static/img/icons/state_down.png',
	    height: 56,
            width: 55,
	}, 
	{
            url: 'images/m3.png',
	    height: 66,
            width: 65,
	},
	{
            url: 'images/m4.png',
	    height: 78,
            width: 77,
	}];
    
    var markers = [];
    var infowindows = [];
    var blinkingMarker = null;

    $.getJSON('/geomap/json', function(data) {
	$('#servicesalerts tbody').empty();
	$('#hostsalerts tbody').empty();
	$('#comments tbody').empty();
	
	if(data) {
	    $.each(data, function(k) {
		// add datacenter icon on the good location
		var location =  new google.maps.LatLng(data[k]['position']['latitude'], data[k]['position']['longitude']);
		var marker = new MarkerWithLabel({
		    position: location,
		    title: k + ' datacenter',
		    map: map,
		    icon: dc_icon,
		    labelClass: 'markerlabels'
		});
		
		marker.h_critical = data[k]['hosts']['down'].length; 
		marker.s_critical = data[k]['services']['critical'].length;
		marker.h_total = data[k]['hosts']['down'].length + data[k]['hosts']['up'].length;  
		marker.s_total = data[k]['services']['ok'].length + data[k]['services']['warning'].length + data[k]['services']['unknown'].length;

		// add a mini table for displaying number of alerts per datacenter
		$.each(['ok', 'critical', 'warning', 'unknown'], function (i, level) {
		    marker.labelContent += '<div class="cell ' + level + '">' + data[k]['services'][level].length + '</div> ';
		});

		// add to alerts table
		d = new Date();
		$.each(['down'], function (i, level) {
		    $.each(data[k]['hosts'][level], function (a_i, alert) {
			last_change = new Date(alert['last_hard_state_change']*1000);
			duration = d - last_change;
			$('#hostsalerts tbody').append('<tr class="alert' + level + '"><td class="sort">' + i + '_' + duration + '</td><td>' + alert['host_name'] + '</td><td>' + durationToStr(duration) + '</td></tr>');
		    });
		});

		// add the informative window
		var infowindow = new google.maps.InfoWindow({
		    content: '<b>' + k + '</b><br/>'
		});

		infowindows[k] = infowindow;

		$.each(['critical'], function (i, level) {
		    $.each(data[k]['services'][level], function (a_i, alert) {
			last_change = new Date(alert['last_hard_state_change']*1000);
			duration = d - last_change;
			tr = $('<tr class="alert' + level + '"><td class="sort">' + i + '_' + duration + '</td><td>' + alert['host_name'] + '</td><td>' + durationToStr(duration) + '</td><td>' + alert['description'] + '</td><td>' + alert['plugin_output'] + '</td></tr>');
			
			tr.click(function() {
			    infowindows[k].open(map, marker);
			});
			
			$('#servicesalerts tbody').append(tr);
		    });
		});
		
		google.maps.event.addListener(marker, 'click', function() {
		    infowindows[k].open(map, this);
		});

		// group markers
		markers.push(marker);

		// add comments
		$.each(data[k]['comments'], function (c_i, comment) {
		    $('#comments tbody').append('<tr class="comment' + comment['entry_type_desc'] + '"><td class="sort">' + comment['entry_time'] + '</td><td>' + dateFormat(comment['entry_time']*1000, 'YYYY-MM-DD HH:mm:ss') + '</td><td>' + comment['host_name'] + '</td><td>' + comment['service_description'] + '</td><td>' + comment['author'] + '</td><td>' + comment['comment'] + '</td></tr>');	    
		});
	    });

	    // sort alerts
	    sortByStateAndDuration('hostsalerts');
	    sortByStateAndDuration('servicesalerts');
	    sortByTime('comments');
	    setBestSize('alertsdetails');
	    setBestSize('commentsdiv');
	    
	    if (markerClusterer) {
		markerClusterer.clearMarkers();
	    }
	    
	    markerClusterer = new MarkerClusterer(map, markers, {
		minimumClusterSize: 1,
		calculator: alerts_count,
		maxZoom: 4,
		styles: styles
	    });
	    
	    daynightoverlay.setDate(new Date());
	    console.log("finish");
	}
    });
    
    setTimeout(refreshMap, 10000);
}

function clearClusters(e) {
    e.preventDefault();
    e.stopPropagation();
    markerClusterer.clearMarkers();
}

function alerts_count(markers) {
    s_critical = 0;
    h_critical = 0;
    s_total = 0;
    h_total = 0;

    for (var i = 0;i < markers.length; i++) {
        s_critical += markers[i].s_critical;
        h_critical += markers[i].h_critical;

        s_total += markers[i].s_total;
	h_total += markers[i].h_total;
    }

    var index = 1;
    if (s_critical > 0 || h_critical > 0) {
	index = 2;
    }

    if (s_critical >= 10 || h_critical >= 10) {
	index = 3;
    }

    if (s_critical >= 20 || h_critical >= 20) {
	index = 4;
    }

    return {
        text: s_critical + ' / ' + h_critical,
        index: index
    };
};

var url = window.location.protocol + '//' + window.location.host + window.location.pathname;
var scriptpath = url.substring(0, url.lastIndexOf('/'));

var markerClusterer = null;
var daynightoverlay = null;
var map = null;

function initialize() {
    var mapOptions = {
        center: new google.maps.LatLng(25, -0.582085),
	//center: new google.maps.LatLng(25, 100),
	zoom: 2,
	mapTypeId: google.maps.MapTypeId.ROADMAP
    };

    map = new google.maps.Map(document.getElementById('alertsmap'), mapOptions);

    daynightoverlay = new DayNightOverlay({
	map: map
    });
     
    refreshMap();
}

$(function(){
    google.maps.event.addDomListener(window, 'load', initialize);
});