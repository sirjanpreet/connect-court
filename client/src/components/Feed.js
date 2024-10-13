import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const Feed = () => {
    const [events, setEvents] = useState([]);
    const [username, setUsername] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        // Fetch feed data including events and user info
        axios.get('/api/feed')
            .then((response) => {
                setEvents(response.data.events); // Events data
                setUsername(response.data.user.username); // Username of the current user
            })
            .catch((error) => {
                console.error('Error fetching feed data:', error);
            });
    }, []);

    const handleSignUp = (eventId) => {
        axios.post(`/api/signup_event/${eventId}`)
            .then(() => {
                // Update the state directly to reflect signup status
                setEvents((prevEvents) =>
                    prevEvents.map((event) =>
                        event.event.event_id === eventId
                            ? { ...event, is_signed_up: true }
                            : event
                    )
                );
            })
            .catch((error) => {
                console.error('Error signing up for the event:', error);
            });
    };

    const handleUnregister = (eventId) => {
        axios.post(`/api/unregister_event/${eventId}`)
            .then(() => {
                // Update the state directly to reflect unregistration status
                setEvents((prevEvents) =>
                    prevEvents.map((event) =>
                        event.event.event_id === eventId
                            ? { ...event, is_signed_up: false }
                            : event
                    )
                );
            })
            .catch((error) => {
                console.error('Error unregistering from the event:', error);
            });
    };

    return (
        <div>
            {/* Navigation Links */}
            <div style={{ textAlign: 'right' }}>
                <button onClick={() => navigate('/profile')}>Edit Profile</button> |
                <button onClick={() => navigate('/discover')}>Discover Users</button> |
                <button onClick={() => navigate('/friends')}>Friends</button> |
                <button onClick={() => navigate('/logout')}>Sign Out</button>
            </div>
            
            {/* Welcome Message */}
            <h1>Welcome to your feed, {username}!</h1>
            <p>You are now signed in.</p>

            {/* Events Section */}
            <h2>Events</h2>
            <button onClick={() => navigate('/create-event')}>Create Event</button>
            <button onClick={() => navigate('/my-events')}>My Events</button>
            <button onClick={() => navigate('/registered-events')}>Registered Events</button>

            <div id="events-container">
                {events.length > 0 ? (
                    events.map((eventData) => (
                        <div key={eventData.event.event_id} className="event-card">
                            <h2>{eventData.event.title}</h2>
                            <p><strong>Organized by:</strong> {eventData.event.organizer_id}</p>
                            <p><strong>Sport:</strong> {eventData.event.sport}</p>
                            <p><strong>Date:</strong> {eventData.event.date}</p>
                            <p><strong>Time:</strong> {eventData.event.start_time} - {eventData.event.end_time}</p>
                            <p><strong>Location:</strong> {eventData.event.city}, {eventData.event.state}</p>
                            <p><strong>Description:</strong> {eventData.event.description}</p>
                            <p><strong>Venue:</strong> {eventData.event.venue}</p>
                            <p><strong>Current signups:</strong> {eventData.current_signups} / {eventData.max_capacity}</p>

                            {eventData.is_signed_up ? (
                                <button onClick={() => handleUnregister(eventData.event.event_id)}>
                                    Unregister
                                </button>
                            ) : (
                                <button onClick={() => handleSignUp(eventData.event.event_id)}>
                                    Sign Up
                                </button>
                            )}
                        </div>
                    ))
                ) : (
                    <p>No events found.</p>
                )}
            </div>
        </div>
    );
};

export default Feed;
