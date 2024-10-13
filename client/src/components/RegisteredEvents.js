import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const RegisteredEvents = () => {
    const [events, setEvents] = useState([]);
    const [username, setUsername] = useState('');
    const navigate = useNavigate(); // Updated to use navigate

    useEffect(() => {
        // Fetch registered events and user data from the backend
        axios.get('/api/registered_events')
            .then((response) => {
                setEvents(response.data.events); // Assuming response.data.events contains the list of events
                setUsername(response.data.user.username); // Assuming response.data.user contains the username
            })
            .catch((error) => {
                console.error('Error fetching registered events:', error);
            });
    }, []);

    const handleUnregister = (eventId) => {
        if (window.confirm('Are you sure you want to unregister from this event?')) {
            axios.post(`/api/unregister_event/${eventId}`)
                .then(() => {
                    // Remove the event from the list after unregistering
                    setEvents(events.filter(event => event.event.id !== eventId));
                })
                .catch((error) => {
                    console.error('Error unregistering from the event:', error);
                });
        }
    };

    return (
        <div>
            {/* Navigation Links */}
            <div style={{ textAlign: 'right' }}>
                <p>Signed in as: {username}</p>
                <button onClick={() => navigate('/profile')}>Edit Profile</button> |
                <button onClick={() => navigate('/discover')}>Discover Users</button> |
                <button onClick={() => navigate('/logout')}>Sign Out</button>
            </div>

            <h1>Registered Events</h1>
            <p>This is where you can see all the events you've signed up for.</p>

            {/* Event Navigation Links */}
            <button onClick={() => navigate('/feed')}>My Feed</button> |
            <button onClick={() => navigate('/my-events')}>My Events</button> |
            <button onClick={() => navigate('/create-event')}>Create Event</button>

            {events.length > 0 ? (
                <ul>
                    {events.map((eventData) => (
                        <div key={eventData.event.id} className="event-card">
                            <li>
                                <h2>{eventData.event.title}</h2>
                                <p><strong>Organized by:</strong> {eventData.event.organizer_id}</p>
                                <p><strong>Sport:</strong> {eventData.event.sport}</p>
                                <p><strong>Date:</strong> {eventData.event.date}</p>
                                <p><strong>Time:</strong> {eventData.event.start_time} - {eventData.event.end_time}</p>
                                <p><strong>Location:</strong> {eventData.event.city}, {eventData.event.state}</p>
                                <p><strong>Description:</strong> {eventData.event.description}</p>
                                <p><strong>Venue:</strong> {eventData.event.venue}</p>
                                <p><strong>Current signups:</strong> {eventData.current_signups} / {eventData.event.max_capacity}</p>

                                {eventData.event.organizer_id === username ? (
                                    <p>You are the organizer of this event.</p>
                                ) : (
                                    <button onClick={() => handleUnregister(eventData.event.id)} className="btn btn-danger">
                                        Unregister
                                    </button>
                                )}
                            </li>
                        </div>
                    ))}
                </ul>
            ) : (
                <p>You have no registered events.</p>
            )}
        </div>
    );
};

export default RegisteredEvents;
