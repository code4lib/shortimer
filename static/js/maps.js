(function($) {

var map = null;

function drawMap() {
    map = L.map('map', {
        center: [38.8951, -77.0363],
        zoom: 3,
        attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>'
    });
    L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom: 22}).addTo(map);
    $.getJSON('/api/v1/map', addMarkers);
}
    
function addMarkers(data) {
    var opts = {
        radius: 8,
        fillColor: "blue",
        color: "blue",
        weight: 1,
        opacity: 1,
        fillOpacity: 0.8
    };

    function onEachFeature(feature, layer) {
        var created = new Date(feature.properties.created).toDateString();
        var text = "<b><a href='/job/" + feature.id + "/'>" + 
          feature.properties.title + "</a></b>" +
          "<br />" + feature.properties.employer +
          "<br />" + created;
        layer.bindPopup(text);
    }

    for (i in data.features) {
        feature = data.features[i];
        L.geoJson(feature, {
            pointToLayer: function (feature, latlng) {
                return L.circleMarker(latlng, opts);
            },
            onEachFeature: onEachFeature
        }).addTo(map);
    }
}

$(document).ready(drawMap);

})(jQuery);
