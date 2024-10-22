document.addEventListener('DOMContentLoaded', () => {
    const accessToken = localStorage.getItem('access');
    const username = localStorage.getItem('username');

    if (accessToken) {
        // Verify token with the server
        fetch('/api/verify-token/', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        })
        .then(response => {
            if (response.ok) {
                // Token is valid
                document.getElementById('loginLink').style.display = 'none';
                document.getElementById('logoutButton').style.display = 'inline-block';
                document.getElementById('username').style.display = 'inline-block';
                document.getElementById('username').innerText = `Hello, ${username}`;
            } else {
                // Token is invalid or expired
                throw new Error('Token invalid or expired');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            // Remove invalid token from local storage
            localStorage.removeItem('access');
            localStorage.removeItem('username');
            document.getElementById('loginLink').style.display = 'inline-block';
            document.getElementById('logoutButton').style.display = 'none';
            document.getElementById('username').style.display = 'none';
        });
    } else {
        // No token found
        document.getElementById('loginLink').style.display = 'inline-block';
        document.getElementById('logoutButton').style.display = 'none';
        document.getElementById('username').style.display = 'none';
    }
});

document.getElementById('logoutButton').addEventListener('click', (event) => {
    event.preventDefault();
    // Clear the local storage on logout
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    localStorage.removeItem('username');
    document.getElementById('loginLink').style.display = 'inline-block';
    document.getElementById('logoutButton').style.display = 'none';
    document.getElementById('username').style.display = 'none';
});




// function downloadSentiment(){
//     const token=localStorage.getItem('access');
//     if(!token){
//         alert('No access token found . please log in again');
//         window.location.href='/login-page/';
//         return;
//     }
//     // const sessionId=document.getElementById("sentiment-session-id").value
//     // if(!sessionId){
//     //     alert('Type your sessionId');
//     //     return
//     // }
//     fetch(downloadSentimentURL,{
//         method:'POST',
//         headers:{
//             'Authorization': `Bearer ${token}`
//         }
//     }).then(response=>{
//         if(response.status===401){
//             alert('session expired. Please log in again.');
//             window.location.href = '/login-page/';
//         }
//         if (response.ok) {
//             console.log("response");
//             return response.blob();
//         }  else {
//             return response.json().then(error => {
//                 throw new Error(error.error || 'Failed to download');
//             });
//         }
//     })
//     .then(blob=>{
//         const url=window.URL.createObjectURL(blob);
//         const a=document.createElement('a');
//         a.href=url;
//         a.download='sentiment_result.xlsx';
//         document.body.appendChild(a);
//         a.click();
//         a.remove();
//         window.URL.revokeObjectURL(URL);
//     })
//     .catch(error=>{
//         console.log('Error:',error);
//     });
// }