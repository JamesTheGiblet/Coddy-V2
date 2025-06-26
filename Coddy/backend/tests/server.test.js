// Coddy/backend/tests/server.test.js
// This file contains integration tests for the Coddy V2 Express backend.
// It uses Jest for the testing framework and Supertest for HTTP assertions.

// Import Supertest to make HTTP requests to the Express app
const request = require('supertest');
// Import the Express app from your server.js file
// Ensure the path is correct relative to this test file.
const app = require('../server'); // Assuming server.js is in the parent directory

// Import Mongoose for database operations in tests
const mongoose = require('mongoose');

// Define a test MongoDB URI
// It's highly recommended to use a separate database for testing to avoid
// polluting your development database.
const TEST_MONGODB_URI = process.env.TEST_MONGODB_URI || 'mongodb://localhost:27017/coddy_test_db';

// Before all tests, connect to the test MongoDB and clear collections
beforeAll(async () => {
    // Connect to the test database
    await mongoose.connect(TEST_MONGODB_URI);
    console.log(`Connected to test MongoDB: ${TEST_MONGODB_URI}`);

    // Clear the test database collections before running tests
    // This ensures a clean state for each test run.
    await mongoose.connection.dropCollection('memories').catch(() => {}); // ignore error if collection doesn't exist
    await mongoose.connection.dropCollection('roadmaps').catch(() => {}); // ignore error if collection doesn't exist
    console.log('Test database collections cleared.');
});

// After all tests, disconnect from MongoDB
afterAll(async () => {
    await mongoose.connection.close();
    console.log('Disconnected from test MongoDB.');
});

describe('Coddy V2 Backend API Tests', () => {

    // Test the root route
    test('GET / should return "Coddy V2 Backend is running!"', async () => {
        const response = await request(app).get('/');
        expect(response.statusCode).toBe(200);
        expect(response.text).toBe('Coddy V2 Backend is running!');
    });

    describe('/api/memory', () => {
        // Test POST a new memory fragment
        test('POST /api/memory should create a new memory fragment', async () => {
            const newMemory = {
                content: 'This is a test memory fragment.',
                tags: ['test', 'jest']
            };
            const response = await request(app)
                .post('/api/memory')
                .send(newMemory)
                .expect(201); // Expect a 201 Created status

            expect(response.body.message).toBe('Memory fragment added');
            expect(response.body.data).toHaveProperty('_id');
            expect(response.body.data.content).toBe(newMemory.content);
            expect(response.body.data.tags).toEqual(expect.arrayContaining(newMemory.tags));
        });

        // Test POST with missing content
        test('POST /api/memory with missing content should return 400', async () => {
            const response = await request(app)
                .post('/api/memory')
                .send({ tags: ['invalid'] })
                .expect(400); // Expect a 400 Bad Request status

            expect(response.body.error).toBe('Memory content is required.');
        });

        // Test GET all memory fragments
        test('GET /api/memory should return a list of memory fragments', async () => {
            // Ensure there's at least one memory from the previous POST test
            const response = await request(app).get('/api/memory').expect(200); // Expect a 200 OK status

            expect(response.body.message).toBe('Memory fragments retrieved');
            expect(Array.isArray(response.body.data)).toBe(true);
            expect(response.body.data.length).toBeGreaterThan(0);
            expect(response.body.data[0]).toHaveProperty('content');
            expect(response.body.data[0]).toHaveProperty('timestamp');
        });
    });

    describe('/api/roadmap', () => {
        // Test POST a new roadmap entry
        test('POST /api/roadmap should create a new roadmap entry', async () => {
            const newRoadmap = {
                phase: 'Phase 1',
                goal: 'Complete core setup',
                status: 'in-progress',
                tasks: ['implement backend', 'create CLI']
            };
            const response = await request(app)
                .post('/api/roadmap')
                .send(newRoadmap)
                .expect(201); // Expect a 201 Created status

            expect(response.body.message).toBe('Roadmap entry added');
            expect(response.body.data).toHaveProperty('_id');
            expect(response.body.data.phase).toBe(newRoadmap.phase);
            expect(response.body.data.goal).toBe(newRoadmap.goal);
        });

        // Test POST with missing phase or goal
        test('POST /api/roadmap with missing phase should return 400', async () => {
            const response = await request(app)
                .post('/api/roadmap')
                .send({ goal: 'Some goal' })
                .expect(400); // Expect a 400 Bad Request status

            expect(response.body.error).toBe('Phase and goal are required for a roadmap entry.');
        });

        // Test GET all roadmap entries
        test('GET /api/roadmap should return a list of roadmap entries', async () => {
            // Ensure there's at least one roadmap entry from the previous POST test
            const response = await request(app).get('/api/roadmap').expect(200); // Expect a 200 OK status

            expect(response.body.message).toBe('Roadmap entries retrieved');
            expect(Array.isArray(response.body.data)).toBe(true);
            expect(response.body.data.length).toBeGreaterThan(0);
            expect(response.body.data[0]).toHaveProperty('phase');
            expect(response.body.data[0]).toHaveProperty('goal');
        });
    });
});
