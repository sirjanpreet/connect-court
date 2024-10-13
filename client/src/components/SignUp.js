import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const SignUp = () => {
    const [formData, setFormData] = useState({
        username: '',
        password: ''
    });
    const navigate = useNavigate();  // Replaces history

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData({
            ...formData,
            [name]: value
        });
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        axios.post('/api/signup', formData)
            .then((response) => {
                // Assuming the API returns a successful sign-up response
                console.log('Account created successfully:', response.data);
                navigate('/signin'); // Use navigate for redirecting after successful sign-up
            })
            .catch((error) => {
                console.error('Error signing up:', error);
                alert('There was an issue creating your account. Please try again.');
            });
    };

    return (
        <div>
            <h1>Create an Account</h1>
            <form onSubmit={handleSubmit}>
                <label htmlFor="username">Username:</label>
                <input
                    type="text"
                    id="username"
                    name="username"
                    value={formData.username}
                    onChange={handleChange}
                    required
                /><br />

                <label htmlFor="password">Password:</label>
                <input
                    type="password"
                    id="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    required
                /><br />

                <button type="submit">Sign Up</button>
            </form>

            <p>Already have an account? <button onClick={() => navigate('/signin')}>Sign In</button></p> {/* Updated to navigate */}
        </div>
    );
};

export default SignUp;
