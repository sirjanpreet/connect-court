import React from 'react';
import { useNavigate } from 'react-router-dom';

const Home = () => {
    const navigate = useNavigate();  // Change history to navigate

    const handleSignIn = () => {
        navigate('/signin');  // Use navigate instead of history.push
    };

    return (
        <div>
            <h1>Welcome to Court Connect!</h1>
            <p>We help people with interests in recreational sports connect.</p>
            <button onClick={handleSignIn}>Sign In</button>
        </div>
    );
};

export default Home;
