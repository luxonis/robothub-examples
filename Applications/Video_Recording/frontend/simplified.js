const sendStartButton = document.getElementById("start-record");
const sendStopButton = document.getElementById("stop-record");


document.getElementById('start-record').addEventListener('click', () => {
    // Start recording logic here
    console.log('Recording started');
    sendStartButton.disabled = true;
    sendStopButton.disabled = false;
    robothubApi.notify("recording_start", {});
});

document.getElementById('stop-record').addEventListener('click', () => {
    // Stop recording logic here
    console.log('Recording stopped');
    sendStartButton.disabled = false;
    sendStopButton.disabled = true;
    robothubApi.notify("recording_stop", {});
});

document.getElementById('send-video-buffer').addEventListener('click', () => {
    // Start recording logic here
    console.log('Sending video buffer');
    robothubApi.notify("send_video_buffer", {});
});

document.getElementById('send-image-event').addEventListener('click', () => {
    // Stop recording logic here
    console.log('Sending image event');
    robothubApi.notify("send_image_event", {});
});
