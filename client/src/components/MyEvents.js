import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const MyEvents = () => {
    const [events, setEvents] = useState([]);
    const navigate = useNavigate(); // Changed 'history' to 'navigate'

    useEffect(() => {
        // Fetch the user's events from the backend
        axios.get('/api/my_events')
            .then((response) => {
                setEvents(response.data.events); // Assuming response.data.events contains the list of events
            })
            .catch((error) => {
                console.error('Error fetching events:', error);
            });
    }, []);

    const handleDelete = (eventId) => {
        if (window.confirm('Are you sure you want to delete this event?')) {
            axios.post(`/api/delete_event/${eventId}`)
                .then(() => {
                    // Reload the events after deletion
                    setEvents(events.filter(event => event.event.id !== eventId));
                })
                .catch((error) => {
                    console.error('Error deleting event:', error);
                });
        }
    };

    return (
        <div>
            {/* Navigation Links */}
            <div style={{ textAlign: 'right' }}>
                <button onClick={() => navigate('/profile')}>Edit Profile</button> |
                <button onClick={() => navigate('/discover')}>Discover Users</button> |
                <button onClick={() => navigate('/logout')}>Sign Out</button>
            </div>

            <h1>My Events</h1>
            <p>These are events that you've created. You can edit them or delete them here.</p>

            <button onClick={() => navigate('/feed')}>My Feed</button> |
            <button onClick={() => navigate('/create-event')}>Create Event</button> |
            <button onClick={() => navigate('/registered-events')}>Registered Events</button>

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

                                {/* Edit Event Button */}
                                <button onClick={() => navigate(`/edit-event/${eventData.event.id}`)} className="btn btn-primary">
                                    Edit Event
                                </button>

                                {/* Delete Event Button */}
                                <button onClick={() => handleDelete(eventData.event.id)} className="btn btn-danger" style={{ marginLeft: '10px' }}>
                                    Delete Event
                                </button>
                            </li>
                        </div>
                    ))}
                </ul>
            ) : (
                <p>You have no events.</p>
            )}
        </div>
    );
};

export default MyEvents;
