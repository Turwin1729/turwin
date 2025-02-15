import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  TextField,
  Button,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import axios from 'axios';

function PatientDashboard({ user }) {
  const [testResults, setTestResults] = useState([]);
  const [username, setUsername] = useState(user.username);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    fetchTestResults();
  }, []);

  const fetchTestResults = async () => {
    try {
      const response = await axios.get(`/api/test-results/${user.id}`);
      setTestResults(response.data);
    } catch (error) {
      setError('Failed to fetch test results');
    }
  };

  const handleUpdateProfile = async () => {
    try {
      const response = await axios.patch(`/api/users/${user.id}`, {
        username: username
      });
      setSuccessMessage('Profile updated successfully');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to update profile');
    }
  };

  const handleProfileImageUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('image', file);

    try {
      await axios.post(`/api/upload-image/${user.id}`, formData);
      setSuccessMessage('Profile image updated successfully');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error) {
      setError('Failed to upload profile image');
    }
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        Patient Dashboard
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {successMessage && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {successMessage}
        </Alert>
      )}

      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Profile
        </Typography>
        <Box sx={{ mb: 2 }}>
          {user.profile_image && (
            <img
              src={`/uploads/${user.profile_image}`}
              alt="Profile"
              style={{ maxWidth: 200, maxHeight: 200, marginBottom: 16 }}
            />
          )}
          <input
            type="file"
            accept="image/*"
            onChange={handleProfileImageUpload}
            style={{ marginBottom: 16, display: 'block' }}
          />
          <TextField
            fullWidth
            label="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            sx={{ mb: 2 }}
          />
          <Button variant="contained" onClick={handleUpdateProfile}>
            Update Profile
          </Button>
        </Box>
      </Paper>

      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          My Test Results
        </Typography>
        {testResults.map((test) => (
          <Accordion key={test.id}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography>{test.test_type} - {test.date}</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography paragraph>
                <strong>Result:</strong> {test.result}
              </Typography>
              {test.image_path && (
                <img
                  src={`/uploads/${test.image_path}`}
                  alt="Test Result"
                  style={{ maxWidth: '100%', maxHeight: 300 }}
                />
              )}
            </AccordionDetails>
          </Accordion>
        ))}
        {testResults.length === 0 && (
          <Typography color="textSecondary">
            No test results available
          </Typography>
        )}
      </Paper>
    </Container>
  );
}

export default PatientDashboard;
