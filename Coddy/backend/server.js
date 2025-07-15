// Coddy/backend/server.js
// This script sets up the Express.js server and connects to MongoDB.
// It exposes basic routes: /api/memory, /api/roadmap, /api/feedback, and /api/pattern.

// Import necessary modules
const express = require('express');
const mongoose = require('mongoose');
const path = require('path'); // Used for serving static files if needed later

// --- Configuration ---
// MongoDB connection URI
// Replace 'mongodb://localhost:27017/coddy_db' with your actual MongoDB URI if it's different.
// For Docker, you might use 'mongodb://mongodb:27017/coddy_db' if your MongoDB service is named 'mongodb'.
// In a test environment (NODE_ENV=test), we'll use a separate test database.
const MONGODB_URI = process.env.NODE_ENV === 'test' ?
                    (process.env.TEST_MONGODB_URI || 'mongodb://localhost:27017/coddy_test_db') :
                    (process.env.MONGODB_URI || 'mongodb://localhost:27017/coddy_db');
const PORT = process.env.PORT || 3000; // Server port

// Initialize Express app
const app = express();

// --- Middleware ---
// Enable CORS for all origins (for development purposes)
// In a production environment, you should restrict this to known origins.
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
    next();
});

// Middleware to parse JSON request bodies
app.use(express.json());

// --- MongoDB Connection ---
// Deprecated options useNewUrlParser and useUnifiedTopology have been removed
// as they are no longer necessary in Mongoose versions 4.0.0 and above.
mongoose.connect(MONGODB_URI)
.then(() => {
    console.log('MongoDB connected successfully to:', MONGODB_URI);
})
.catch(err => {
    console.error('MongoDB connection error:', err.message);
    // Only exit the process if not in a test environment.
    // In test environment, Jest will handle process exit.
    if (process.env.NODE_ENV !== 'test') {
        process.exit(1);
    }
});

// Define Mongoose Schemas and Models
// Schema for Memory fragments
const memorySchema = new mongoose.Schema({
    timestamp: { type: Date, default: Date.now },
    content: { type: String, required: true },
    tags: [String],
    session_id: { type: String }, // To link memories to a specific session
    user_id: { type: String }    // Added user_id to Memory schema
});
const Memory = mongoose.model('Memory', memorySchema);

// Schema for Roadmap entries
const roadmapSchema = new mongoose.Schema({
    phase: { type: String, required: true },
    goal: { type: String, required: true },
    status: { type: String, default: 'planned' }, // e.g., 'planned', 'in-progress', 'completed'
    tasks: [String]
});
const Roadmap = mongoose.model('Roadmap', roadmapSchema);

// Schema for Feedback
const feedbackSchema = new mongoose.Schema({
    timestamp: { type: Date, default: Date.now },
    type: { type: String, enum: ['bug', 'feature_request', 'general'], default: 'general' },
    message: { type: String, required: true },
    user_id: { type: String },
    session_id: { type: String },
    metadata: { type: mongoose.Schema.Types.Mixed } // For any extra context
});
const Feedback = mongoose.model('Feedback', feedbackSchema);

// Schema for Patterns (from PatternOracle analysis)
const patternSchema = new mongoose.Schema({
    timestamp: { type: Date, default: Date.now },
    pattern_type: { type: String, required: true }, // e.g., 'coding_habit', 'refactoring_preference'
    description: { type: String },
    data: { type: mongoose.Schema.Types.Mixed }, // The pattern data
    user_id: { type: String }
});
const Pattern = mongoose.model('Pattern', patternSchema);

// --- Routes ---

// Root route for basic server check
app.get('/', (req, res) => {
    res.send('Coddy V2 Backend is running!');
});

// API route for Memory
// GET all memory fragments
app.get('/api/memory', async (req, res) => {
    try {
        const memories = await Memory.find({});
        res.json({ message: 'Memory fragments retrieved', data: memories });
    } catch (error) {
        console.error('Error fetching memories:', error);
        res.status(500).json({ error: 'Failed to retrieve memory fragments' });
    }
});

// POST a new memory fragment
app.post('/api/memory', async (req, res) => {
    // Destructure user_id from req.body as well
    const { content, tags, session_id, user_id } = req.body;
    if (!content) {
        return res.status(400).json({ error: 'Memory content is required.' });
    }
    try {
        // Pass user_id to the new Memory instance
        const newMemory = new Memory({ content, tags, session_id, user_id });
        await newMemory.save();
        res.status(201).json({ message: 'Memory fragment added', data: newMemory });
    } catch (error) {
        console.error('Error adding memory:', error);
        res.status(500).json({ error: 'Failed to add memory fragment' });
    }
});

// API route for Roadmap
// GET all roadmap entries
app.get('/api/roadmap', async (req, res) => {
    try {
        const roadmapEntries = await Roadmap.find({});
        res.json({ message: 'Roadmap entries retrieved', data: roadmapEntries });
    } catch (error) {
        console.error('Error fetching roadmap:', error);
        res.status(500).json({ error: 'Failed to retrieve roadmap entries' });
    }
});

// POST a new roadmap entry
app.post('/api/roadmap', async (req, res) => {
    const { phase, goal, status, tasks } = req.body;
    if (!phase || !goal) {
        return res.status(400).json({ error: 'Phase and goal are required for a roadmap entry.' });
    }
    try {
        const newRoadmapEntry = new Roadmap({ phase, goal, status, tasks });
        await newRoadmapEntry.save();
        res.status(201).json({ message: 'Roadmap entry added', data: newRoadmapEntry });
    } catch (error) {
        console.error('Error adding roadmap entry:', error);
        res.status(500).json({ error: 'Failed to add roadmap entry' });
    }
});

// NEW API route for Feedback
// POST a new feedback entry
app.post('/api/feedback', async (req, res) => {
    const { type, message, user_id, session_id, metadata } = req.body;
    if (!message) {
        return res.status(400).json({ error: 'Feedback message is required.' });
    }
    try {
        const newFeedback = new Feedback({ type, message, user_id, session_id, metadata });
        await newFeedback.save();
        res.status(201).json({ message: 'Feedback submitted successfully', data: newFeedback });
    } catch (error) {
        console.error('Error submitting feedback:', error);
        res.status(500).json({ error: 'Failed to submit feedback' });
    }
});

// NEW API route for Patterns
// POST a new pattern entry (e.g., from PatternOracle analysis)
app.post('/api/pattern', async (req, res) => {
    const { pattern_type, description, data, user_id } = req.body;
    if (!pattern_type || !data) {
        return res.status(400).json({ error: 'Pattern type and data are required.' });
    }
    try {
        const newPattern = new Pattern({ pattern_type, description, data, user_id });
        await newPattern.save();
        res.status(201).json({ message: 'Pattern stored successfully', data: newPattern });
    } catch (error) {
        console.error('Error storing pattern:', error);
        res.status(500).json({ error: 'Failed to store pattern' });
    }
});

// GET all patterns
app.get('/api/pattern', async (req, res) => {
    try {
        const patterns = await Pattern.find({});
        res.json({ message: 'Patterns retrieved', data: patterns });
    } catch (error) {
        console.error('Error fetching patterns:', error);
        res.status(500).json({ error: 'Failed to retrieve patterns' });
    }
});


// --- Server Start ---
// Only start the server if this script is run directly (not imported by a test runner)
if (require.main === module) {
    app.listen(PORT, () => {
        console.log(`Coddy V2 Backend server listening on port ${PORT}`);
        console.log(`Access at http://localhost:${PORT}`);
    });
}


// Export the app for testing purposes
module.exports = app;