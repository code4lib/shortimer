
add_markers = function(data) {
    for (obj in data) {
        add_marker(data[obj]);
    }
};

add_marker = function(obj) {
    var post_date = new Date(obj.post_date).toDateString();
    //create the marker
    var marker =  L.marker([obj.location__latitude, obj.location__longitude], {riseOnHover : true});
    //give it a popup
    marker.bindPopup("<b><a href='/job/" +obj.pk + "/'>" +obj.title + "</a></b>" +
        "<br />" + obj.employer__name +
        "<br />" + post_date);
    marker.on('mouseover', function() { this.openPopup(); });
    oldest_job = post_date; //for setting the oldest job
    //ad it to the cluster
    markers.addLayer(marker);
    return marker;
};

button_text = function(marker_count, oldest){
    smallText = "<button class='btn' id='moreJobs'><i class='icon-map-marker'></i> More Jobs</button>";
    bigText = "Jobs since <br />"+ oldest.slice(4)+ "</br>" + smallText;
    //use up less space
    return text = ($("html").width() < 400)? smallText : bigText;

};

zoom_of_if_no_points = function (map, layers) {
    if (!view_contains_point(map, layers)) {
    map.zoomOut();
    zoom_of_if_no_points(map, layers);
    }
}

view_contains_point = function(map,layers) {
    for (m in layers) {
        if (map.getBounds().contains(layers[m].getLatLng())) {
            return true;
        }
    }
    return false;
}


var olderJobs = L.Control.extend({
    //adds control button for adding lder jobs w/ ajax
    options: {
        position: 'topright'
    },
    onAdd: function (map) {
        // create the control container with a particular class name
        var container = L.DomUtil.create('div', 'btn');
        container.innerHTML = button_text(marker_count,oldest_job);
        L.DomEvent.addListener(container,'click',function() {
            $.ajax({
                url : "/map/more/" + marker_count + "/"
            }).done(
                function(data) {
                    add_markers(data);
                    marker_count += data.length;
                    container.innerHTML = button_text(marker_count, oldest_job);
                }
            )});
        return container;
    }
});

