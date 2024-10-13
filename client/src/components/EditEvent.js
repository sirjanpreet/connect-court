import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate, useParams } from 'react-router-dom';

const EditEvent = () => {
    const { eventId } = useParams();  // Get event ID from the route params
    const navigate = useNavigate();  // Updated to use `navigate`

    const [eventData, setEventData] = useState({
        title: '',
        description: '',
        city: '',
        state: '',
        venue: '',
        date: '',
        start_time: '',
        end_time: ''
    });

    useEffect(() => {
        // Fetch the event data to populate the form
        axios.get(`/api/event/${eventId}`)
            .then(response => {
                const event = response.data.event;
                setEventData({
                    title: event.title,
                    description: event.description,
                    city: event.city,
                    state: event.state,
                    venue: event.venue,
                    date: event.date,
                    start_time: event.start_time,
                    end_time: event.end_time
                });
            })
            .catch(error => {
                console.error('Error fetching event data:', error);
            });
    }, [eventId]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setEventData((prevState) => ({
            ...prevState,
            [name]: value
        }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        // Update the event using the API
        axios.post(`/api/edit_event/${eventId}`, eventData)
            .then(() => {
                navigate('/my-events');  // Updated to use `navigate`
            })
            .catch(error => {
                console.error('Error updating event:', error);
            });
    };

    return (
        <div>
            <h1>Edit Event: {eventData.title}</h1>
            <form onSubmit={handleSubmit}>
                <input
                    type="text"
                    name="title"
                    value={eventData.title}
                    onChange={handleChange}
                    required
                />
                <textarea
                    name="description"
                    value={eventData.description}
                    onChange={handleChange}
                    required
                />
                <input
                    type="text"
                    name="city"
                    value={eventData.city}
                    onChange={handleChange}
                    required
                />
                <input
                    type="text"
                    name="state"
                    value={eventData.state}
                    onChange={handleChange}
                    required
                />
                <input
                    type="text"
                    name="venue"
                    value={eventData.venue}
                    onChange={handleChange}
                    required
                />
                <input
                    type="date"
                    name="date"
                    value={eventData.date}
                    onChange={handleChange}
                    required
                />
                <input
                    type="time"
                    name="start_time"
                    value={eventData.start_time}
                    onChange={handleChange}
                    required
                />
                <input
                    type="time"
                    name="end_time"
                    value={eventData.end_time}
                    onChange={handleChange}
                    required
                />
                <button type="submit">Update Event</button>
            </form>
            <button onClick={() => navigate('/my-events')}>Cancel</button> {/* Updated to use `navigate` */}
        </div>
    );
};

export default EditEvent;
