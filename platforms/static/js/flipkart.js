
// common code start ================================================================================================

function disablePage() {
    console.log("Disabling page...");
    document.querySelectorAll('button, input, a').forEach(element => {
        element.disabled = true;
        element.style.pointerEvents = 'none';
        element.style.opacity = '0.5';
    });
}

function enablePage() {
    console.log("enabling page....")
    document.querySelectorAll('button, input, a').forEach(element => {
        element.disabled = false;
        element.style.pointerEvents = 'auto';
        element.style.opacity = '1';
    });
    isScriptRunning=false;
}
// common code end ================================================================================================
// ----------------------download template start ---------------------------------------------------------------------------------

    async function downloadTemplate() {
        const token = localStorage.getItem('access'); // Get the access token from local storage
        if (!token) {
            alert('No access token found. Please log in again.');
            window.location.href = '/login-page/';
            return;
        }
        try {
            disablePage()
            const response = await fetch(downloadTemplateUrl, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            if (response.status === 401) {
                // Unauthorized: Redirect to login page
                alert('Session expired. Please log in again.');
                window.location.href = '/login-page/'; // Adjust the URL as needed
            }
            if (response.ok) {
                const blob = await response.blob(); // Get the file as a blob
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'excel_template_flipkart.xlsx';
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url); // Clean up the URL object
                enablePage();
            }  
            else {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to download');
                enablePage();
            }
        } catch (error) {
            console.error('Error:', error);
            enablePage();
        }
    }
    

//--------------------upload file start------------------------------------------------------------------------------------
async function uploadFile() {
    const token = localStorage.getItem('access');
    if (!token) {
        alert('No access token found. Please log in again.');
        window.location.href = '/login-page/';
        return;
    }
    const formData = new FormData(document.getElementById('uploadForm'));
    document.getElementById('spinner').style.display='block';
    disablePage()
    try {
        const response = await fetch(uploadFlipkartUrl, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value // If needed
            },
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                alert('File uploaded successfully.');
                document.getElementById('spinner').style.display = 'none'; 
                enablePage();
                setTimeout(() => {
                    window.location.reload();
                }, 2000); 
            } else {
                alert('Error: ' + data.error);
                document.getElementById('spinner').style.display = 'none';  // Hide spinner after failure
                enablePage(); 
            }
        } else if (response.status === 401) {
            alert('Session expired. Please log in again.');
            window.location.href = '/login-page/';
        } else {
            const errorData = await response.json();
            document.getElementById('spinner').style.display = 'none';  // Hide spinner after failure
            enablePage(); 
            throw new Error(errorData.error || 'Failed to upload file.');
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('spinner').style.display = 'none';  // Hide spinner on error
        enablePage();
        if (error.message.includes('Cannot read properties of undefined')) {
            alert('An unexpected error occurred. Please try again later.');
        } else {
            alert('An error occurred: ' + error.message);
        }
    }
}

// running scrappping  script js code start================================================================================================

window.onbeforeunload = function () {
    if (isScriptRunning) {
        return "Are you sure you want to refresh? Your ongoing operation will be stopped.";
    }
};
let isScriptRunning = false;


function runScrappingScript() {
    const token = localStorage.getItem('access');
    if (!token) {
        alert('No access token found. Please log in again.');
        window.location.href = '/login-page/';
        return;
    }
    const sessionId=document.getElementById("scrapping-session-id").value
    if(!sessionId){
        alert('Type your sessionId');
        return
    }
    isScriptRunning=true;
    disablePage();
    // Disable the button and show the spinner
    document.getElementById('run-scrappingScript-btn').disabled = true;
    document.getElementById('spinner').style.display = 'block';
    document.getElementById('scrappingScript-status').innerText = "Running...";

    fetch(runScrappingScriptUrl, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken  // Use the CSRF token passed from the template
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
            document.getElementById('scrappingScript-status').style.backgroundColor = 'red';
            throw new Error('Network response was not ok');
        }
        document.getElementById('scrappingScript-status').style.backgroundColor = 'red';
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
           console.log("success");
        } else if (data.status === 'error') {
            document.getElementById('run-scrappingScript-btn').disabled = false;  // Re-enable button if an error occurs
            document.getElementById('scrappingScript-status').style.backgroundColor = 'orange';
        }
        enablePage();
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('spinner').style.display = 'none';
        document.getElementById('scrappingScript-status').innerText = "An error occurred.";
        document.getElementById('run-scrappingScript-btn').disabled = false;  // Re-enable button if an error occurs
        document.getElementById('scrappingScript-status').style.backgroundColor = 'red';
        enablePage();
    });
}
// running scrapping script  js code end================================================================================================



function runSentimentScript(){
    const token = localStorage.getItem('access');
    if (!token) {
        alert('No access token found. Please log in again.');
        window.location.href = '/login-page/';
        return;
    }
    const sessionId=document.getElementById("sentiment-session-id").value
    if(!sessionId){
        alert('Type your sessionId');
        return
    }
    isScriptRunning=true;
    disablePage();
    document.getElementById('spinner').style.display = 'block';
    document.getElementById('sentimentScript-status').innerText = "Running...";
    fetch(runSentimentUrl, {
       method:'POST', 
       headers :{
        'Authorization': `Bearer ${token}`,
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        'Content-Type': 'application/json' // Use the CSRF token passed from the template
       },
       body: JSON.stringify({
        sessionId: sessionId,
    })
    })
    .then(response => {
        if (response.status === 401) {
            isScriptRunning=false
            alert('Session expired. Please log in again.');
            window.location.href = '/login-page/';
            return;
        }
        if (!response.ok) {
            document.getElementById('sentimentScript-status').style.backgroundColor = 'red';
            throw new Error('Network response was not ok');
        }
        document.getElementById('sentimentScript-status').style.backgroundColor = 'green';
        return response.json();
    })
    .then(data => {
        document.getElementById('spinner').style.display = 'none';
        const statusElement = document.getElementById('sentimentScript-status');
        statusElement.innerText = data.message;
        statusElement.style.display = 'flex';
        statusElement.style.justifyContent = 'center';
        statusElement.style.backgroundColor = 'orange';
        statusElement.style.color = 'black';
        statusElement.style.border = '2px solid darkorange';

        if (data.status === 'success') {
           console.log("success");
        } else if (data.status === 'error') {
            document.getElementById('run-sentimentScript-btn').disabled = false;  // Re-enable button if an error occurs
            document.getElementById('sentimentScript-status').style.backgroundColor = 'orange';
        }
        enablePage();
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('spinner').style.display = 'none';
        document.getElementById('sentimentScript-status').innerText = "An error occurred.";
        document.getElementById('run-sentimentScript-btn').disabled = false;  // Re-enable button if an error occurs
        document.getElementById('sentimentScript-status').style.backgroundColor = 'red';
        enablePage();
    });

}

