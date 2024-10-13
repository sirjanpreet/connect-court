import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const Discover = () => {
    const [users, setUsers] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [friendships, setFriendships] = useState({
        accepted: [],
        sent: [],
        received: []
    });
    const navigate = useNavigate();  // Update to use `navigate`

    useEffect(() => {
        // Fetch users data based on search query
        axios.get('/api/discover', {
            params: { q: searchQuery }
        })
        .then((response) => {
            setUsers(response.data.users); // Assuming response.data.users is an array of users
            setFriendships(response.data.friendships); // Assuming friendships data is included in the response
        })
        .catch((error) => {
            console.error('Error fetching users:', error);
        });
    }, [searchQuery]);

    const handleSearchChange = (e) => {
        setSearchQuery(e.target.value);
    };

    const handleReset = () => {
        setSearchQuery('');
    };

    const sendFriendRequest = (userId) => {
        axios.post(`/api/send_request/${userId}`)
        .then(() => {
            // Refresh the user list after sending request
            setSearchQuery(searchQuery);
        })
        .catch((error) => {
            console.error('Error sending friend request:', error);
        });
    };

    const acceptFriendRequest = (userId) => {
        axios.post(`/api/accept_request/${userId}`)
        .then(() => {
            // Refresh the user list after accepting request
            setSearchQuery(searchQuery);
        })
        .catch((error) => {
            console.error('Error accepting friend request:', error);
        });
    };

    return (
        <div>
            {/* Back to Feed Button */}
            <button onClick={() => navigate('/feed')}> {/* Updated to `navigate` */}
                &larr; Back to Feed
            </button>

            {/* Search Form */}
            <form onSubmit={(e) => e.preventDefault()} style={{ marginBottom: '20px' }}>
                <input
                    type="text"
                    placeholder="Search..."
                    value={searchQuery}
                    onChange={handleSearchChange}
                />
                <button type="submit">Search</button>
                <button type="button" onClick={handleReset} style={{ marginLeft: '10px' }}>
                    Reset
                </button>
            </form>

            <h1>Discover Users</h1>
            <div className="container" style={containerStyle}>
                {users.map(user => (
                    <div key={user.id} className="card" style={cardStyle}>
                        <h2>{user.name}</h2>
                        <p><strong>Location:</strong> {user.location_city}, {user.location_state}</p>
                        <p><strong>Bio:</strong> {user.bio}</p>
                        <p><strong>Sports:</strong> {user.sports}</p>
                        <p><strong>Interests:</strong> {user.interests}</p>

                        {friendships.accepted.includes(user.id) && (
                            <p>Your Friend</p>
                        )}
                        {friendships.sent.includes(user.id) && (
                            <p>Friend Request Sent</p>
                        )}
                        {friendships.received.includes(user.id) && (
                            <button onClick={() => acceptFriendRequest(user.id)}>
                                Accept Friend Request
                            </button>
                        )}
                        {!friendships.accepted.includes(user.id) &&
                         !friendships.sent.includes(user.id) &&
                         !friendships.received.includes(user.id) && (
                            <button onClick={() => sendFriendRequest(user.id)}>
                                Add Friend
                            </button>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};

// Styles (can be moved to an external CSS file)
const containerStyle = {
    display: 'flex',
    flexWrap: 'wrap',
    justifyContent: 'space-around'
};

const cardStyle = {
    border: '1px solid #ccc',
    borderRadius: '10px',
    width: '300px',
    margin: '15px',
    padding: '15px',
    boxShadow: '2px 2px 12px rgba(0, 0, 0, 0.1)'
};

export default Discover;
