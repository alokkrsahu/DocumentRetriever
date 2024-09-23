<script>
    import { onMount, onDestroy } from 'svelte';
    
    export let projectName;
    // Removed unused export of username
    
    let socket;
    let members = [];
    let messages = [];
    let newMessage = '';
    let connectionStatus = 'Disconnected';

onMount(() => {
    connectWebSocket();
});

onDestroy(() => {
    if (socket) {
        socket.close();
    }
});

function connectWebSocket() {
    const wsUrl = `ws://localhost:8000/ws/chat/${encodeURIComponent(projectName)}/`;
    console.log('Attempting to connect to WebSocket:', wsUrl);
    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        connectionStatus = 'Connected';
        console.log('WebSocket connected');
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Received message:', data);

        switch (data.type) {
            case 'chat_message':
                messages = [...messages, { username: data.username, message: data.message }];
                break;
            case 'user_join':
                members = [...members, { username: data.username, isOnline: true, isBusy: false }];
                break;
            case 'user_leave':
                members = members.filter(member => member.username !== data.username);
                break;
            case 'user_status':
                members = members.map(member => 
                    member.username === data.username 
                        ? { ...member, isOnline: data.isOnline, isBusy: data.isBusy }
                        : member
                );
                break;
        }
    };

    socket.onclose = (event) => {
        connectionStatus = 'Disconnected';
        console.log('WebSocket disconnected:', event.code, event.reason);
        setTimeout(connectWebSocket, 5000);  // Attempt to reconnect after 5 seconds
    };

    socket.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

function sendMessage() {
    if (newMessage.trim() && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            type: 'chat_message',
            message: newMessage
        }));
        newMessage = '';
    }
}
</script>

<div class="online-members-container">
    <div class="connection-status">
        Status: {connectionStatus}
    </div>
    <div class="online-members">
        <h3>Online Members:</h3>
        <ul>
            {#each members as member}
                <li>{member.username} - {member.isOnline ? 'Online' : 'Offline'} {member.isBusy ? '(Busy)' : ''}</li>
            {/each}
        </ul>
    </div>
    <div class="chat">
        <h3>Chat:</h3>
        <div class="messages">
            {#each messages as message}
                <p><strong>{message.username}:</strong> {message.message}</p>
            {/each}
        </div>
        <div class="input-area">
            <input type="text" bind:value={newMessage} placeholder="Type a message..." on:keypress={(e) => e.key === 'Enter' && sendMessage()}>
            <button on:click={sendMessage}>Send</button>
        </div>
    </div>
</div>

<style>
.online-members-container {
    display: flex;
    flex-direction: column;
    height: 100%;
}
.connection-status {
    background-color: #f0f0f0;
    padding: 10px;
    margin-bottom: 10px;
    border-radius: 4px;
    font-weight: bold;
}
.online-members {
    border: 1px solid #ccc;
    padding: 1em;
    margin-bottom: 1em;
    background-color: #f9f9f9;
    border-radius: 4px;
}
.chat {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
}
.messages {
    flex-grow: 1;
    overflow-y: auto;
    border: 1px solid #ccc;
    padding: 1em;
    margin-bottom: 1em;
    background-color: white;
    border-radius: 4px;
}
.input-area {
    display: flex;
}
input {
    flex-grow: 1;
    padding: 10px;
    font-size: 16px;
    border: 1px solid #ccc;
    border-radius: 4px 0 0 4px;
}
button {
    padding: 10px 20px;
    font-size: 16px;
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 0 4px 4px 0;
    cursor: pointer;
    transition: background-color 0.3s;
}
button:hover {
    background-color: #45a049;
}
h3 {
    color: #333;
    margin-bottom: 10px;
}
ul {
    list-style-type: none;
    padding: 0;
}
li {
    margin-bottom: 5px;
}
</style>
