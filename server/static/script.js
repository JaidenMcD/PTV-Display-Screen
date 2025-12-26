// Update stopId whenever the user types/selects a stop
const stopInput = document.getElementById('Train-Stop-Select');
const stopIdInput = document.getElementById('Train-Stop-Id');
const datalist = document.getElementById('Train-Stops-Select');

stopInput.addEventListener('input', () => {
    const opt = Array.from(datalist.options).find(o => o.value === stopInput.value);
    stopIdInput.value = opt ? opt.dataset.stopId : '';
});


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
            // Use stop_name as the visible value, stop_id as a data attribute if needed
            o.value = s.stop_name;
            o.dataset.stopId = s.stop_id;
            datalist.appendChild(o);
        });
    });

    get_display_types(option);
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
    const stopName = document.getElementById('Train-Stop-Select').value;
    const stopId = document.getElementById('Train-Stop-Id').value;
    const displayType = document.querySelector('input[name="display-option"]:checked')?.value;

    if (!transitType || !stopName || !displayType || !stopId) {
        alert('Please select transit type, stop, and display type');
        return;
    }

    const response = await fetch('/api/send-to-display', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transitType, stopName, stopId, displayType })
    });

    const data = await response.json();
    alert(data.message || 'Sent to display');
}
