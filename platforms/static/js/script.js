document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const uploadButton = document.getElementById('uploadButton');
    const responseMessage = document.getElementById('responseMessage');

    uploadForm.onsubmit = function(event) {
        event.preventDefault(); // Prevent the default form submission

        const formData = new FormData(uploadForm);

        fetch(uploadForm.action, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                uploadButton.style.display = 'none';
                responseMessage.style.display = 'block';
            } else {
                alert('An error occurred: ' + data.error);
            }
        })
        .catch(error => {
            console.error('There was a problem with the fetch operation:', error);
            alert('An error occurred while uploading the file.');
        });
    };
});
