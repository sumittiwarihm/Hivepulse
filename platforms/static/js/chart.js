function showGraph() {
    const sessionID = document.querySelector('#session-id').value;  // Get session ID from input field
    if(!sessionID){
        alert('enter session id');
        return ;
    }

    // Fetch the CSRF token from the hidden input field
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // Fetch data from the backend using the correct URL
    fetch(getDataForPlaystoreGraph, {  // 'getDataForGraph' is dynamically set in the HTML file
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken  // Pass the CSRF token in the headers
        },
        body: JSON.stringify({ sessionId: sessionID })  // Ensure 'sessionId' matches the backend
    })
    .then(res => {
        if (!res.ok) {
            throw new Error('Network response was not ok: ' + res.statusText);
        }
        return res.json();  // Parse the JSON from the response
    })
    .then(resData => {
        const data = resData.data;  // Access the "data" key from the response
        const chartContainer = document.querySelector('#myChart');  // Parent container for all charts
        
        // Clear the chart container to avoid appending duplicate charts
        chartContainer.innerHTML = '';

            // Configure options for the pie chart
            const options = {
                container: chartContainer,  // Use the dynamically created div as container

                // Prepare the data for the pie chart
                data: data,

            
                series: [
                    { type: 'bar', xKey: 'appId', yKey: 'positiveCount', yName: 'Positive' },
                    { type: 'bar', xKey: 'appId', yKey: 'negativeCount', yName: 'Negative' },
                    { type: 'bar', xKey: 'appId', yKey: 'neutralCount', yName: 'Neutral' },
                ],
            };

            // Render the pie chart for each sentiment count
            agCharts.AgCharts.create(options);
        
    })
    .catch(error => console.error('Error:', error));  // Handle errors gracefully
}






    // Define the chart series
                // series: [
                //     {
                //         type: 'pie',
                //         angleKey: 'count',
                //         calloutLabelKey: 'sentiment',
                //         sectorLabelKey: 'count',
                //         sectorLabel: {
                //             color: 'white',
                //             fontWeight: 'bold'
                //         }
                //     }
                // ],



