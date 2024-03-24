const sendDetectionButton = document.getElementById('send-detection');
let lastClickTime = 0;

sendDetectionButton.addEventListener('click', function () {
    const currentTime = Date.now();
    if (currentTime - lastClickTime < 1000) {
        return; // Ignore clicks that are less than 1 second apart
    }
    lastClickTime = currentTime;

    // Disable the button for 1 second
    sendDetectionButton.disabled = true;
    setTimeout(function () {
        sendDetectionButton.disabled = false;
    }, 1000);

    // Add your code to be executed when the button is clicked here
    robothubApi.notify('take_picture', {})
});
