// app/static/js/camera.js

document.addEventListener('DOMContentLoaded', function() {
    const video = document.getElementById('video');
    const captureButton = document.getElementById('capture-button');
    const canvas = document.getElementById('canvas');
    const loginForm = document.getElementById('login-form');
    const imageInput = document.getElementById('image-data');

    // Access the webcam
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(function(stream) {
                video.srcObject = stream;
                video.play();
            })
            .catch(function(err) {
                console.error("Error accessing the camera: ", err);
                alert("Could not access the camera. Please allow camera access or use a different device.");
            });
    } else {
        alert("getUserMedia not supported by your browser.");
    }

    // Capture the image
    captureButton.addEventListener('click', function() {
        const context = canvas.getContext('2d');
        const width = video.videoWidth;
        const height = video.videoHeight;

        if (width && height) {
            canvas.width = width;
            canvas.height = height;
            context.drawImage(video, 0, 0, width, height);

            // Convert the image to base64
            const dataURL = canvas.toDataURL('image/png');
            imageInput.value = dataURL;

            // Show the captured image (optional)
            // You can display it to the user before submitting
            // For now, we proceed to submit the form
            loginForm.style.display = 'block';
            loginForm.submit();
        } else {
            alert("Unable to capture image. Please try again.");
        }
    });
});
