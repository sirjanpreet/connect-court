import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const Profile = () => {
    const [profileData, setProfileData] = useState({
        name: '',
        phone: '',
        email: '',
        bio: '',
        age: '',
        sports: '',
        interests: '',
        location_city: '',
        location_state: '',
        languages: '',
        gender: '',
        pronouns: '',
        school_work: '',
        profile_picture: null, // for the file input
    });
    const [states, setStates] = useState([]);
    const [profilePicturePreview, setProfilePicturePreview] = useState(null);
    const navigate = useNavigate(); // Updated for useNavigate

    useEffect(() => {
        // Fetch user profile and states data from the backend
        axios.get('/api/profile')
            .then((response) => {
                const { user, states } = response.data;
                setProfileData({
                    name: user.name || '',
                    phone: user.phone || '',
                    email: user.email || '',
                    bio: user.bio || '',
                    age: user.age || '',
                    sports: user.sports || '',
                    interests: user.interests || '',
                    location_city: user.location_city || '',
                    location_state: user.location_state || '',
                    languages: user.languages || '',
                    gender: user.gender || '',
                    pronouns: user.pronouns || '',
                    school_work: user.school_work || '',
                    profile_picture: null,
                });
                setStates(states);
                setProfilePicturePreview(user.profile_picture);
            })
            .catch((error) => {
                console.error('Error fetching profile data:', error);
            });
    }, []);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setProfileData((prevState) => ({
            ...prevState,
            [name]: value,
        }));
    };

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        setProfileData((prevState) => ({
            ...prevState,
            profile_picture: file,
        }));
        setProfilePicturePreview(URL.createObjectURL(file)); // Preview selected image
    };

    const handleSubmit = (e) => {
        e.preventDefault();
    
        const formData = new FormData();
        for (const key in profileData) {
            if (profileData[key]) {
                formData.append(key, profileData[key]);
            }
        }
    
        // Debugging: Check what formData contains
        for (let pair of formData.entries()) {
            console.log(pair[0], pair[1]);
        }
    
        // Post the updated profile data
        axios.post('/api/profile', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        })
        .then(() => {
            // Redirect to the feed page after saving
            navigate('/feed');
        })
        .catch((error) => {
            console.error('Error saving profile:', error);
        });
    };
    

    return (
        <div>
            <h1>Edit Profile</h1>
            {/* Back to Feed Button */}
            <button onClick={() => navigate('/feed')} style={{ marginBottom: '10px' }}>
                &larr; Back to Feed
            </button>

            <form onSubmit={handleSubmit} encType="multipart/form-data">
                <label htmlFor="name">Name:</label>
                <input
                    type="text"
                    id="name"
                    name="name"
                    value={profileData.name}
                    onChange={handleChange}
                /><br />

                <label htmlFor="phone">Phone:</label>
                <input
                    type="text"
                    id="phone"
                    name="phone"
                    value={profileData.phone}
                    onChange={handleChange}
                /><br />

                <label htmlFor="email">Email:</label>
                <input
                    type="text"
                    id="email"
                    name="email"
                    value={profileData.email}
                    onChange={handleChange}
                /><br />

                <label htmlFor="bio">Bio:</label>
                <textarea
                    id="bio"
                    name="bio"
                    value={profileData.bio}
                    onChange={handleChange}
                ></textarea><br />

                <label htmlFor="age">Age:</label>
                <input
                    type="number"
                    id="age"
                    name="age"
                    value={profileData.age}
                    onChange={handleChange}
                /><br />

                <label htmlFor="sports">Sports:</label>
                <input
                    type="text"
                    id="sports"
                    name="sports"
                    value={profileData.sports}
                    onChange={handleChange}
                /><br />

                <label htmlFor="interests">Interests:</label>
                <input
                    type="text"
                    id="interests"
                    name="interests"
                    value={profileData.interests}
                    onChange={handleChange}
                /><br />

                <label htmlFor="location_city">City:</label>
                <input
                    type="text"
                    id="location_city"
                    name="location_city"
                    value={profileData.location_city}
                    onChange={handleChange}
                /><br />

                <label htmlFor="location_state">State:</label>
                <select
                    id="location_state"
                    name="location_state"
                    value={profileData.location_state}
                    onChange={handleChange}
                >
                    <option value="" disabled>Select your state</option>
                    {states.map((state) => (
                        <option key={state.code} value={state.code}>
                            {state.name}
                        </option>
                    ))}
                </select><br />

                <label htmlFor="languages">Languages:</label>
                <input
                    type="text"
                    id="languages"
                    name="languages"
                    value={profileData.languages}
                    onChange={handleChange}
                /><br />

                <label htmlFor="gender">Gender:</label>
                <input
                    type="text"
                    id="gender"
                    name="gender"
                    value={profileData.gender}
                    onChange={handleChange}
                /><br />

                <label htmlFor="pronouns">Pronouns:</label>
                <input
                    type="text"
                    id="pronouns"
                    name="pronouns"
                    value={profileData.pronouns}
                    onChange={handleChange}
                /><br />

                <label htmlFor="school_work">School/Work:</label>
                <input
                    type="text"
                    id="school_work"
                    name="school_work"
                    value={profileData.school_work}
                    onChange={handleChange}
                /><br />

                <label htmlFor="profile_picture">Profile Picture:</label>
                <input
                    type="file"
                    id="profile_picture"
                    name="profile_picture"
                    onChange={handleFileChange}
                /><br />

                <button type="submit">Save Profile</button>
            </form>

            {profilePicturePreview && (
                <div>
                    <h2>Your Profile Picture</h2>
                    <img src={profilePicturePreview} alt="Profile Preview" style={{ maxWidth: '150px' }} />
                </div>
            )}
        </div>
    );
};

export default Profile;
