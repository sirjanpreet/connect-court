import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const SignIn = () => {
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
        axios.post('/api/signin', formData)
            .then((response) => {
                // Assuming the API returns a successful login response
                console.log('Signed in successfully:', response.data);
                navigate('/feed'); // Use navigate for redirecting after successful sign-in
            })
            .catch((error) => {
                console.error('Error signing in:', error);
                alert('Invalid username or password. Please try again.');
            });
    };

    return (
        <div>
            <h1>Sign In to Court Connect</h1>
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

                <button type="submit">Sign In</button>
            </form>

            <p>Don't have an account? <button onClick={() => navigate('/signup')}>Sign Up</button></p> {/* Updated to navigate */}
        </div>
    );
};

export default SignIn;
