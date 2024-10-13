import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';

// Import all the components
import Home from './components/Home';
import SignIn from './components/SignIn';
import SignUp from './components/SignUp';
import Feed from './components/Feed';
import Profile from './components/Profile';
import MyEvents from './components/MyEvents';
import RegisteredEvents from './components/RegisteredEvents';
import Discover from './components/Discover';
import Friends from './components/Friends';
import EditEvent from './components/EditEvent';
import CreateEvent from './components/CreateEvent';
import Chat from './components/Chat';

function App() {
    return (
        <Router>
            <Routes>
                {/* Home Page */}
                <Route exact path="/" element={<Home />} />

                {/* Auth Pages */}
                <Route path="/signin" element={<SignIn />} />
                <Route path="/signup" element={<SignUp />} />

                {/* Feed & Profile */}
                <Route path="/feed" element={<Feed />} />
                <Route path="/profile" element={<Profile />} />

                {/* Event Management */}
                <Route path="/my-events" element={<MyEvents />} />
                <Route path="/registered-events" element={<RegisteredEvents />} />
                <Route path="/create-event" element={<CreateEvent />} />
                <Route path="/edit-event/:eventId" element={<EditEvent />} />

                {/* Discover and Friends */}
                <Route path="/discover" element={<Discover />} />
                <Route path="/friends" element={<Friends />} />

                {/* Chat */}
                <Route path="/chat" element={<Chat />} />
            </Routes>
        </Router>
    );
}

export default App;
