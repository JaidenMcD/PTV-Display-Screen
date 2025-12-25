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
    get_display_types(option)
    return;
}


function get_display_types(transit_type) {
    let displays = []
    if (transit_type == 'Metropolitan-Train') {
        displays = ['platform']
    }
    else if (transit_type == 'Tram') {
        displays = ['tram_display']
    }
    else {
        console.log('Not a valid transit type')
    }
    div = document.getElementById('display-select-div');
    div.innerHTML = "";
    displays.forEach(d => {

            const label = document.createElement('label');

            const o = document.createElement('input');
            o.value = d;
            o.name = 'display-option'
            o.type = 'radio'
            label.appendChild(o);
            label.appendChild(document.createTextNode(` ${d}`));
            div.appendChild(label);
            div.appendChild(document.createElement('br'));
        });
    
}

async function send_to_display() {
    const transitType = document.querySelector('input[name="option"]:checked')?.value;
    const stop = document.getElementById('Train-Stop-Select').value;
    const displayType = document.querySelector('input[name="display-option"]:checked')?.value;

    if (!transitType || !stop || !displayType) {
        alert('Please select transit type, stop, and display type');
        return;
    }

    const response = await fetch('/api/send-to-display', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transitType, stop, displayType })
    });

    const data = await response.json();
    alert(data.message || 'Sent to display');
}