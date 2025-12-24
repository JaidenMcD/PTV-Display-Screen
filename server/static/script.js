function get_train_stops(type) {
    url = "/api/stops?type=" + type
    return fetch(url)
        .then(r => r.json())
        .catch(() => []);
}

function change_transit_type(option) {
    get_train_stops(option).then(stops => {
        const datalist = document.getElementById('Train-Stops-Select');
        datalist.innerHTML = '';
        stops.forEach(s => {
            const o = document.createElement('option');
            o.value = s;
            datalist.appendChild(o);
        });
    });
    return;
}