import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const Friends = () => {
    const [friends, setFriends] = useState([]);
    const navigate = useNavigate();  // Use `navigate` instead of `history`

    useEffect(() => {
        // Fetch the list of friends from the backend
        axios.get('/api/friends')
            .then((response) => {
                setFriends(response.data.friends); // Assuming response.data.friends contains the list of friends
            })
            .catch((error) => {
                console.error('Error fetching friends:', error);
            });
    }, []);

    const handleStartChat = (friendId) => {
        axios.post('/api/start_chat', { friend_id: friendId })
            .then(() => {
                // Use `navigate` to go to the generic chat page
                navigate('/chat');
            })
            .catch((error) => {
                console.error('Error starting chat:', error);
            });
    };

    return (
        <div>
            <h1>Your Friends</h1>
            {/* Back to Feed Button */}
            <button onClick={() => navigate('/feed')} style={{ display: 'inline-block', marginBottom: '10px' }}>
                &larr; Back to Feed
            </button>

            {friends.length > 0 ? (
                friends.map((friend) => (
                    <div key={friend.id} style={friendCardStyle}>
                        <h2>{friend.name}</h2>
                        <p><strong>Phone:</strong> {friend.phone}</p>
                        <p><strong>Email:</strong> {friend.email}</p>
                        <p><strong>City:</strong> {friend.location_city}, {friend.location_state}</p>
                        <p><strong>Sports:</strong> {friend.sports}</p>
                        <p><strong>Interests:</strong> {friend.interests}</p>

                        {/* Button to initiate chat */}
                        <button onClick={() => handleStartChat(friend.id)}>Chat</button>
                    </div>
                ))
            ) : (
                <p>You have no friends added yet.</p>
            )}
        </div>
    );
};

// Styles for the friend card
const friendCardStyle = {
    border: '1px solid #ccc',
    padding: '10px',
    marginBottom: '10px'
};

export default Friends;
