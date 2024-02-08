// script.js
/* For index.html */

// TODO: If a user clicks to create a chat, create an auth key for them
// and save it. Redirect the user to /chat/<chat_id>
function createChat() {

}

/* For room.html */

// TODO: 
// POST to the API when the user posts a new message.
function postMessage() {
  const room_id = window.location.pathname.split('/').pop(); 
  // Get the message from the textarea
  const messageBody = document.getElementById('messageInput').value; 

  // Check if the messageBody is not empty
  if (messageBody.trim().length === 0) {
    alert("Please enter a message.");
    return;
  }

  fetch(`/api/rooms/${room_id}/messages/post`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      // Include API key in the request headers if your API requires authentication
      'Authorization': `Bearer ${WATCH_PARTY_API_KEY}`,
    },
    body: JSON.stringify({ body: messageBody }),
  })
  .then(response => {
    if (response.ok) {
      console.log('Message posted successfully');
      document.getElementById('messageInput').value = ''; // Clear the textarea
      getMessages(); // Refresh messages to show the new one
    } else {
      console.error('Failed to post message');
      response.json().then(data => {
        console.error('Error:', data.error);
      });
    }
  })
  .catch(error => console.error('Error posting message:', error));
}

// Fetch the list of existing chat messages.
function getMessages() {
  // Assuming URL pattern is /rooms/{room_id}
  const room_id = window.location.pathname.split('/').pop(); 

  // connect to the flask endpoint "get_room_messages"
  fetch(`/api/rooms/${room_id}/messages`)
    .then(response => response.json())
    .then(messages => {
      const messagesContainer = document.querySelector('.messages');
      messagesContainer.innerHTML = ''; // Clear existing messages
      messages.forEach(message => {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');

        const authorElement = document.createElement('div');
        authorElement.classList.add('author');
        authorElement.textContent = `${message.author}: `;

        const contentElement = document.createElement('div');
        contentElement.classList.add('content');
        contentElement.textContent = message.body;
        
        messageElement.appendChild(authorElement);
        messageElement.appendChild(contentElement);
        
        messagesContainer.appendChild(messageElement);
      });
    })
    .catch(error => console.error('Error fetching messages:', error));
}

// Automatically poll for new messages on a regular interval.
function startMessagePolling() {
  getMessages(); // Fetch immediately
  setInterval(getMessages, 100); // Fetch every 5 seconds
}


// Function to show the edit UI
function showEditUI() {
  document.querySelector('.edit').classList.remove('hide');
  document.querySelector('.display').classList.add('hide');
}

// Function to hide the edit UI and revert to display mode
function hideEditUI() {
  document.querySelector('.edit').classList.add('hide');
  document.querySelector('.display').classList.remove('hide');
}

// Function to save the new room name
function saveRoomName(roomId) {
  const newName = document.getElementById('editRoomName').value;
  
  // Use fetch to send a POST request to update the room name
  fetch(`/api/rooms/${roomId}/update`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${WATCH_PARTY_API_KEY}`,
      // Include other necessary headers, such as authorization if needed
    },
    body: JSON.stringify({ name: newName })
  })
  .then(response => {
    if (response.ok) {
      return response.json();
    }
    throw new Error('Failed to update room name.');
  })
  .then(data => {
    console.log('Room name updated successfully:', data);
    // Update the display with the new room name
    document.querySelector('.roomName').textContent = newName;
    // Hide the edit UI
    hideEditUI();
  })
  .catch(error => {
    console.error('Error:', error);
  });
}

/* For profile.html */

function updateUsername() {
  const newUsername = document.getElementById('usernameInput').value;
  fetch('/api/user/update/username', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${WATCH_PARTY_API_KEY}`,
    },
    body: JSON.stringify({ new_username: newUsername }),
  })
  .then(response => response.json())
  .then(data => {
    alert('Username updated successfully');
  })
  .catch(error => console.error('Error updating username:', error));
}

function updatePassword() {
  const newPassword = document.getElementById('passwordInput').value;
  fetch('/api/user/update/password', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${WATCH_PARTY_API_KEY}`,
    },
    body: JSON.stringify({ new_password: newPassword }),
  })
  .then(response => response.json())
  .then(data => {
    alert('Password updated successfully');
  })
  .catch(error => console.error('Error updating password:', error));
}


