const getControl = (id) => {
    return document.getElementById(id)
}

const updateDropdown = (dropdown, options) => {
    // Create option elements for every retrieved option
    optionElements = options.map(option => {
        const element = document.createElement('rh-option');

        if (dropdown.id == 'camera')
        {
            element.innerText = option.name
            element.mxid = option.mxid
        } else {
            element.innerText = option
        }
        return element
    })
    // Replace old contents
    dropdown.innerHTML = ''
    for (const element of optionElements) {
        dropdown.appendChild(element)
    }

    
    // if (!dropdown.selected || !optionElements.map(e => e.innerText).includes(dropdown.selected.innerText)) {
    dropdown.select(optionElements[0])
}

// Update camera stream source
const updateStreamSource = (stream, source) => {
    vid = document.querySelector(`#${stream}-container>div>rh-video`)
    const newKey = `${source}-stream/${vid.streamKey.split('/')[1]}`
    // Don't update if the source is already set
    if (vid.getAttribute('stream-key') == newKey) {
        return;
    };
    vid.setAttribute('stream-key', newKey)
    const overlayToggle = vid.parentElement.parentElement.parentElement.querySelector('.overlay-toggle')
    switch (source) {
    case 'color':
    case 'stereo':
        overlayToggle.style.position = 'relative'
        overlayToggle.style.visibility = 'visible'
        break;
    case 'left':
    case 'right':
        overlayToggle.style.position = 'absolute'
        overlayToggle.style.visibility = 'hidden'
    }
    overlayToggle.children[0].innerText = source == 'stereo' ? 'Colormap' : 'Detections'
}

// Update camera stream resolutions
const updateStreamResolutions = (stream, resolutions) => {
    updateDropdown(getControl(`${stream}-resolution`), resolutions)
}

// Update camera stream key to show the selected camera's stream
const updateStreamKey = (id) => {
    let videos = document.querySelectorAll('rh-video')
    for (let vid of videos) {
        const newKey = `${vid.streamKey.split('/')[0]}/${id}`
        // Don't update if the source is already set
        if (vid.getAttribute('stream-key') == newKey) {
            continue;
        };
        vid.setAttribute('stream-key', newKey)
    }
}

const notify = (option, value) => {
    robothubApi.notify('set', { 'deviceId': deviceId(), 'option': option, 'value': value })
}

const request = (option, cb) => {
    robothubApi.request({'option': option, 'deviceId': deviceId() }, 'get', 10000).then(cb)
}

let slowedValues = {}
let slowedIntervals = {}

// Only send updates every 250 ms to prevent overloading the agent
const rateLimitedNotify = (id, value, rate = 250) => {
    slowedValues[id] = value
    if (!slowedIntervals[id]) {
        slowedIntervals[id] = setInterval(() => {
            clearInterval(slowedIntervals[id])
            slowedIntervals[id] = null
            notify(id, slowedValues[id])
        }, rate);
    };
}

// Create depth hover tooltips for stereo streams, and remove them for other streams
const setupHoverDepth = () => {
    for (let stream of document.querySelectorAll('rh-video')) {
        const container = stream.parentElement.parentElement
        const tooltip = container.querySelector('.depth-tooltip')
        let updateInterval = null

        // Show or hide the tooltip when the mouse enters or leaves
        container.onmouseenter = (event) => {
            tooltip.style.visibility = 'hidden'
            updateInterval = setInterval(() => {
                robothubApi.request({'deviceId': deviceId(), 'option': 'depth'}, 'get', 10000).then((resp) => {
                    let [x, y, z] = resp.payload
                    x /= 1000
                    y /= 1000
                    z /= 1000
                    distance = Math.sqrt(x * x + y * y + z * z)
                    tooltip.innerText = `${distance.toFixed(2)} m`
                })
            }, 200)
        }

        container.onmouseleave = (event) => {
            tooltip.style.visibility = 'hidden'
            if (updateInterval != null) {
                clearInterval(updateInterval)
            }
        }
        
        // Update the position of the tooltip and send it to the app
        container.onmousemove = (event) => {
            tooltip.style.visibility = 'visible'
            const rect = container.getBoundingClientRect()
            const localX = event.x - rect.x
            const localY = event.y - rect.y
            tooltip.style.top = `${localY + 10}px`
            tooltip.style.left = `${localX + 10}px`

            rateLimitedNotify('depth-query', { 'x': localX / rect.width, 'y': localY / rect.height }, 200)
        }
    }

    const other = document.querySelectorAll("rh-video[stream-key^='color-stream'], rh-video[stream-key^='left-stream'], rh-video[stream-key^='right-stream']")
    for (let stream of other) {
        const container = stream.parentElement.parentElement
        container.onmouseenter = null
        container.onmouseleave = null
        container.onmousemove = null
    }
}

// Update stream state indicator
const updateStreamState = (stream, state) => {
    let display = state == 'Connected' ? 'none' : '';
    container = stream.parentElement.parentElement
    container.querySelector('.stream-status>rh-text').innerText = state
    container.querySelector('.stream-status').style.display = display
}

const updateStreamStates = (state) => {
    for (const vid of document.querySelectorAll('rh-video')) {
        updateStreamState(vid, state)
    }
}

const refreshVideo = (vid) => {
    copy = vid.cloneNode(true)
    parent = vid.parentElement
    vid.remove()
    parent.appendChild(copy)
}

const refreshAllVideos = () => {
    for (const vid of document.querySelectorAll('rh-video')) {
        refreshVideo(vid)
    }
}

// Extract the id of the currently selected camera
const deviceId = () => {
    try {
        return getControl('camera').selected.mxid
    } catch {
        return ''
    }
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

const updateConfig = (config) => {
    console.error("update config", config)
    config.forEach(setting => {
        let control = getControl(setting.id)
        switch (control.localName) {
            case 'rh-select':
                updateDropdown(control, setting.data)
                break;
            case 'rh-toggle':
                control.setAttribute('on', setting.data)
                break
            case 'rh-slider':
                control.setAttribute('value', setting.data)
                break
        }
    })
}

const updateResolutions = () => {
    request('resolutions', (resp) => {
        topStream = getControl('top-stream').selected.innerText
        botStream = getControl('bot-stream').selected.innerText
        updateStreamResolutions('top', topStream == 'color' ? resp.payload.color : resp.payload.mono)
        updateStreamResolutions('bot', botStream == 'color' ? resp.payload.color : resp.payload.mono)
    })
}

const updateOverlay = (stream, overlay, event) => {
    if (overlay == 'Detections') {
        updateStreamSource(stream, event.value ? 'nn' : 'color')
        refreshVideo(getControl(`${stream}-video`))
    }
}

robothubApi.onConnectedWithApp(() => {
    request('devices', (resp) => {
        updateDropdown(getControl('camera'), resp.payload)
        // updateStreamKey(getControl('camera').selected.mxid)
        updateStreamStates('Connected')
    })
    setupHoverDepth()
})

let firstTimeCounter = 0

// Update the source of all video to be the newly selected camera
robothubApi.whenSelected('camera', (event) => {
    console.error('camera selected', getControl('camera').selected.mxid)
    request('config', (resp) => {
        firstTimeCounter = 0
        updateConfig(resp.payload)
        updateStreamKey(getControl('camera').selected.mxid)
        refreshAllVideos()
    })
});

robothubApi.whenSelected('top-stream', (event) => {
    updateResolutions()
    const stream = event.selected.innerText
    updateStreamSource('top', stream)
    rateLimitedNotify(event.target.id, stream, 500)
    if (firstTimeCounter++ > 8)
    updateStreamStates('Applying changes')

});
robothubApi.whenSelected('bot-stream', (event) => {
    updateResolutions()
    const stream = event.selected.innerText
    updateStreamSource('bot', stream)
    rateLimitedNotify(event.target.id, stream, 500)
    if (firstTimeCounter++ > 8)
    updateStreamStates('Applying changes')
});

robothubApi.whenSelected('top-resolution', (event) => {
    rateLimitedNotify(event.target.id, event.selected.innerText, 500)
    if (firstTimeCounter++ > 8)
    updateStreamStates('Applying changes')
});
robothubApi.whenSelected('bot-resolution', (event) => {
    rateLimitedNotify(event.target.id, event.selected.innerText, 500)
    if (firstTimeCounter++ > 8)
    updateStreamStates('Applying changes')
});

robothubApi.onNotification((e) => {
    console.error("Got notification with id", e.payload.deviceId, deviceId())
    if (e.payload.deviceId != deviceId()) {
        return;
    }
    updateStreamStates('Connected')
    refreshAllVideos()
})

robothubApi.whenSlid('ir-strength', (event) => {
    rateLimitedNotify(event.target.id, event.value)
})
robothubApi.whenSlid('detection-threshold', (event) => {
    rateLimitedNotify(event.target.id, event.value)
})

robothubApi.whenToggled('temporal-filter', (event) => {
    rateLimitedNotify(event.target.id, event.value)
});
robothubApi.whenToggled('top-overlay', (event) => {
    const overlay = event.target.previousElementSibling.innerText
    notify(overlay.toLowerCase(), event.value)
    updateOverlay('top', overlay, event)
});
robothubApi.whenToggled('bot-overlay', (event) => {
    const overlay = event.target.previousElementSibling.innerText
    notify(overlay.toLowerCase(), event.value)
    updateOverlay('bot', overlay, event)
});
