import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const CreateEvent = () => {
    const [formData, setFormData] = useState({
        title: '',
        city: '',
        state: '',
        sport: '',
        description: '',
        venue: '',
        max_capacity: '',
        date: '',
        start_time: '',
        end_time: ''
    });

    const navigate = useNavigate();  // Use navigate instead of history

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prevState) => ({
            ...prevState,
            [name]: value
        }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();

        // Send the form data to the Flask API for event creation
        axios.post('/api/create_event', formData)
            .then((response) => {
                console.log('Event created:', response.data);
                navigate('/feed');  // Use navigate instead of history.push to go to the feed page
            })
            .catch((error) => {
                console.error('Error creating event:', error);
            });
    };

    return (
        <div>
            <h1>Create a New Event</h1>

            <form onSubmit={handleSubmit}>
                <input
                    type="text"
                    name="title"
                    placeholder="Event Title"
                    value={formData.title}
                    onChange={handleChange}
                    required
                />
                <input
                    type="text"
                    name="city"
                    placeholder="City"
                    value={formData.city}
                    onChange={handleChange}
                    required
                />
                <input
                    type="text"
                    name="state"
                    placeholder="State"
                    value={formData.state}
                    onChange={handleChange}
                    required
                />
                <input
                    type="text"
                    name="sport"
                    placeholder="Sport"
                    value={formData.sport}
                    onChange={handleChange}
                    required
                />
                <textarea
                    name="description"
                    placeholder="Description"
                    value={formData.description}
                    onChange={handleChange}
                    required
                />
                <input
                    type="text"
                    name="venue"
                    placeholder="Venue"
                    value={formData.venue}
                    onChange={handleChange}
                    required
                />
                <input
                    type="number"
                    name="max_capacity"
                    placeholder="Max Capacity"
                    value={formData.max_capacity}
                    onChange={handleChange}
                    required
                />
                <input
                    type="date"
                    name="date"
                    value={formData.date}
                    onChange={handleChange}
                    required
                />
                <input
                    type="time"
                    name="start_time"
                    value={formData.start_time}
                    onChange={handleChange}
                    required
                />
                <input
                    type="time"
                    name="end_time"
                    value={formData.end_time}
                    onChange={handleChange}
                    required
                />
                <button type="submit">Create Event</button>
            </form>

            <button onClick={() => navigate('/feed')}>
                Back to Feed
            </button>
        </div>
    );
};

export default CreateEvent;
