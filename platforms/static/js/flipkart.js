// Variables to track progress
let isScriptRunning = false;
let fileUploaded = false;
let scrapingScriptRun = false;
let sentimentScriptRun = false;
let currentStep = 1;
function updateProgressBar(step) {
    const progressBar = document.getElementById('progress-bar');
    const currentStepText = document.getElementById('current-step');
    const totalSteps = 4;
    const percentage = (step / totalSteps) * 100;
    progressBar.style.width = percentage + '%';
    currentStepText.innerText = step;
}
// Function to go to the next step
function goToNextStep(currentStep) {
    var currentStepDiv = document.getElementById('step-' + currentStep);
    var nextStepDiv = document.getElementById('step-' + (currentStep + 1));

    if (currentStep === 1) {
        // No validation needed for step 1
        currentStepDiv.style.display = 'none';
        nextStepDiv.style.display = 'block';
        updateProgressBar(currentStep + 1);
    } else if (currentStep === 2) {
        // Validate that the file has been uploaded before moving to next step
        if (fileUploaded) {
            currentStepDiv.style.display = 'none';
            nextStepDiv.style.display = 'block';
            updateProgressBar(currentStep + 1);
        } else {
            alert('Please upload the file before proceeding to the next step.');
        }
    } else if (currentStep === 3) {
        // Validate that the scraping script has been run successfully
        if (scrapingScriptRun) {
            currentStepDiv.style.display = 'none';
            nextStepDiv.style.display = 'block';
            updateProgressBar(currentStep + 1);
        } else {
            alert('Please run the scraping script before proceeding to the next step.');
        }
    }
}

// Function to go to the previous step
function goToPreviousStep(currentStep) {
    var currentStepDiv = document.getElementById('step-' + currentStep);
    var previousStepDiv = document.getElementById('step-' + (currentStep - 1));
    currentStepDiv.style.display = 'none';
    previousStepDiv.style.display = 'block';
}

// Function to handle 'Finish' button
function finishProcess() {
    if (sentimentScriptRun) {
        alert('Process completed!');
        // Redirect to home or wherever you want
        window.location.href = '/';
    } else {
        alert('Please complete the previous steps before finishing.');
    }
}

// Common Functions
function disablePage() {
    console.log("Disabling page...");
    document.querySelectorAll('button, input, a').forEach(element => {
        element.disabled = true;
        element.style.pointerEvents = 'none';
        element.style.opacity = '0.5';
    });
}

function enablePage() {
    console.log("Enabling page...");
    document.querySelectorAll('button, input, a').forEach(element => {
        element.disabled = false;
        element.style.pointerEvents = 'auto';
        element.style.opacity = '1';
    });
    isScriptRunning = false;
}

// Download Template
function downloadTemplate() {
    const token = localStorage.getItem('access');
    if (!token) {
        alert('No access token found. Please log in again.');
        window.location.href = '/login-page/';
        return;
    }

    disablePage();
    fetch(downloadTemplateUrl, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (response.status === 401) {
            alert('Session expired. Please log in again.');
            window.location.href = '/login-page/';
        }
        if (response.ok) {
            return response.blob();
        } else {
            return response.json().then(error => {
                throw new Error(error.error || 'Failed to download');
            });
        }
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'excel_template_flipkart.xlsx';
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        enablePage();
    })
    .catch(error => {
        console.error('Error:', error);
        enablePage();
    });
}

// Upload File
async function uploadFile() {
    const token = localStorage.getItem('access');
    if (!token) {
        alert('No access token found. Please log in again.');
        window.location.href = '/login-page/';
        return;
    }
    
    const formData = new FormData(document.getElementById('uploadForm'));
    document.getElementById('spinner').style.display = 'block';
    disablePage();
    try {
        const response = await fetch(uploadFlipkartUrl, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            document.getElementById('spinner').style.display = 'none';
            enablePage();

            if (data.success) {
                alert('File uploaded successfully.');
                fileUploaded = true;
                // Show the session ID in the popup
                document.getElementById('sessionIdText').textContent = data.sessionId;
                document.getElementById('sessionModal').style.display = 'block';
                document.getElementById('overlay').style.display = 'block';
                // Auto-fill the session ID in the next steps
                document.getElementById('scrapping-session-id').value = data.sessionId;
                document.getElementById('sentiment-session-id').value = data.sessionId;
            } else {
                alert('Error: ' + data.error);
            }
        } else if (response.status === 401) {
            alert('Session expired. Please log in again.');
            window.location.href = '/login-page/';
        } else {
            const errorData = await response.json();
            document.getElementById('spinner').style.display = 'none';
            enablePage();
            throw new Error(errorData.error || 'Failed to upload file.');
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('spinner').style.display = 'none';
        enablePage();
        alert('An error occurred: ' + error.message);
    }
}

// Close Modal Function
document.getElementById('closeModal').onclick = function() {
    document.getElementById('sessionModal').style.display = 'none';
    document.getElementById('overlay').style.display = 'none';
};

// Run Scrapping Script
function runScrappingScript() {
    const token = localStorage.getItem('access');
    if (!token) {
        alert('No access token found. Please log in again.');
        window.location.href = '/login-page/';
        return;
    }
    const sessionId = document.getElementById("scrapping-session-id").value;
    if (!sessionId) {
        alert('Type your session ID');
        return;
    }
    isScriptRunning = true;
    disablePage();
    document.getElementById('run-scrappingScript-btn').disabled = true;
    document.getElementById('spinner').style.display = 'block';
    document.getElementById('scrappingScript-status').innerText = "Running...";

    fetch(runScrappingScriptUrl, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            sessionId: sessionId,
        })
    })
    .then(response => {
        if (response.status === 401) {
            alert('Session expired. Please log in again.');
            window.location.href = '/login-page/';
            return;
        }
        if (!response.ok) {
            document.getElementById('scrappingScript-status').style.backgroundColor = 'red';
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        document.getElementById('spinner').style.display = 'none';
        const statusElement = document.getElementById('scrappingScript-status');
        statusElement.innerText = data.message;
        statusElement.style.display = 'flex';
        statusElement.style.justifyContent = 'center';
        statusElement.style.backgroundColor = 'orange';
        statusElement.style.color = 'black';
        statusElement.style.border = '2px solid darkorange';

        if (data.status === 'success') {
            scrapingScriptRun = true;
        } else if (data.status === 'error') {
            document.getElementById('run-scrappingScript-btn').disabled = false;
            document.getElementById('scrappingScript-status').style.backgroundColor = 'orange';
        }
        enablePage();
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('spinner').style.display = 'none';
        document.getElementById('scrappingScript-status').innerText = "An error occurred.";
        document.getElementById('run-scrappingScript-btn').disabled = false;
        document.getElementById('scrappingScript-status').style.backgroundColor = 'red';
        enablePage();
    });
}

// Run Sentiment Script
function runSentimentScript() {
    const token = localStorage.getItem('access');
    if (!token) {
        alert('No access token found. Please log in again.');
        window.location.href = '/login-page/';
        return;
    }
    const sessionId = document.getElementById("sentiment-session-id").value;
    if (!sessionId) {
        alert('Type your session ID');
        return;
    }
    isScriptRunning = true;
    disablePage();
    document.getElementById('spinner').style.display = 'block';
    document.getElementById('sentimentScript-status').innerText = "Running...";

    fetch(runSentimentUrl, {
       method: 'POST', 
       headers: {
        'Authorization': `Bearer ${token}`,
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        'Content-Type': 'application/json'
       },
       body: JSON.stringify({
           sessionId: sessionId,
       })
    })
    .then(response => {
        if (response.status === 401) {
            isScriptRunning = false;
            alert('Session expired. Please log in again.');
            window.location.href = '/login-page/';
            return;
        }
        if (!response.ok) {
            document.getElementById('sentimentScript-status').style.backgroundColor = 'red';
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        document.getElementById('spinner').style.display = 'none';
        const statusElement = document.getElementById('sentimentScript-status');
        statusElement.innerText = data.message;
        statusElement.style.display = 'flex';
        statusElement.style.justifyContent = 'center';
        statusElement.style.backgroundColor = 'green';
        statusElement.style.color = 'black';
        statusElement.style.border = '2px solid darkorange';

        if (data.status === 'success') {
            sentimentScriptRun = true;
        } else if (data.status === 'error') {
            document.getElementById('run-sentimentScript-btn').disabled = false;
            document.getElementById('sentimentScript-status').style.backgroundColor = 'orange';
        }
        enablePage();
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('spinner').style.display = 'none';
        document.getElementById('sentimentScript-status').innerText = "An error occurred.";
        document.getElementById('run-sentimentScript-btn').disabled = false;
        document.getElementById('sentimentScript-status').style.backgroundColor = 'red';
        enablePage();
    });
}

// Warn user if script is running and they try to close/refresh
window.onbeforeunload = function () {
    if (isScriptRunning) {
        return "Are you sure you want to refresh? Your ongoing operation will be stopped.";
    }
};
