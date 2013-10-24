(function($) {

var map = null;

function drawMap() {
    map = L.map('map', {
        center: [38.8951, -77.0363],
        zoom: 2,
        attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>'
    });
    L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom: 22}).addTo(map);
    $.getJSON('/api/v1/map', addMarkers);
}
    
function addMarkers(data) {
    var opts = {
        radius: 4,
        fillColor: "red",
        color: "red",
        weight: 1,
        opacity: 1,
        fillOpacity: 0.2
    };

    function addPopup(feature, layer) {
        var created = new Date(feature.properties.created).toDateString();
        var text = "<b><a target='_new' href='" + feature.id + "'>" + 
          feature.properties.title + "</a></b>" +
          "<br />" + 
          '<a target="_new" href="' + feature.properties.employer_url + '">' + 
          feature.properties.employer +
          '</a>' + 
          "<br />" + created;
        layer.bindPopup(text);
    }

    for (i in data.features) {
        feature = data.features[i];
        L.geoJson(feature, {
            pointToLayer: function (feature, latlng) {
                return L.circleMarker(latlng, opts);
            },
            onEachFeature: addPopup
        }).addTo(map);
    }

}

$(document).ready(drawMap);

})(jQuery);
