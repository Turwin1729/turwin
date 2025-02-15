import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Box,
  Alert
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import axios from 'axios';

function DoctorDashboard({ user }) {
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [testResults, setTestResults] = useState({});
  const [addTestOpen, setAddTestOpen] = useState(false);
  const [newTest, setNewTest] = useState({
    test_type: '',
    result: '',
    date: new Date().toISOString().split('T')[0]
  });
  const [error, setError] = useState('');

  useEffect(() => {
    fetchPatients();
  }, []);

  const fetchPatients = async () => {
    try {
      const response = await axios.get('/api/users/patients');
      setPatients(response.data);
    } catch (error) {
      setError('Failed to fetch patients');
    }
  };

  const fetchTestResults = async (patientId) => {
    try {
      const response = await axios.get(`/api/test-results/${patientId}`);
      setTestResults({
        ...testResults,
        [patientId]: response.data
      });
    } catch (error) {
      setError('Failed to fetch test results');
    }
  };

  const handleAddTest = async () => {
    try {
      const testData = {
        ...newTest,
        patient_id: selectedPatient.id,
        doctor_id: user.id
      };
      await axios.post('/api/test-results', testData);
      setAddTestOpen(false);
      setNewTest({
        test_type: '',
        result: '',
        date: new Date().toISOString().split('T')[0]
      });
      fetchTestResults(selectedPatient.id);
    } catch (error) {
      setError('Failed to add test result');
    }
  };

  const handleFileUpload = async (event, testId) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('image', file);
    formData.append('test_result_id', testId);

    try {
      await axios.post(`/api/upload-image/${selectedPatient.id}`, formData);
      fetchTestResults(selectedPatient.id);
    } catch (error) {
      setError('Failed to upload image');
    }
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        Doctor Dashboard
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Paper elevation={3} sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Patients
        </Typography>
        <List>
          {patients.map((patient) => (
            <ListItem key={patient.id}>
              <ListItemText 
                primary={patient.username}
                secondary={
                  <Button
                    variant="outlined"
                    onClick={() => {
                      setSelectedPatient(patient);
                      fetchTestResults(patient.id);
                    }}
                  >
                    View Test Results
                  </Button>
                }
              />
              <Button
                variant="contained"
                onClick={() => {
                  setSelectedPatient(patient);
                  setAddTestOpen(true);
                }}
              >
                Add Test Result
              </Button>
            </ListItem>
          ))}
        </List>

        {selectedPatient && testResults[selectedPatient.id] && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="h6" gutterBottom>
              Test Results for {selectedPatient.username}
            </Typography>
            {testResults[selectedPatient.id].map((test) => (
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
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => handleFileUpload(e, test.id)}
                    style={{ marginTop: 10 }}
                  />
                </AccordionDetails>
              </Accordion>
            ))}
          </Box>
        )}

        <Dialog open={addTestOpen} onClose={() => setAddTestOpen(false)}>
          <DialogTitle>Add Test Result</DialogTitle>
          <DialogContent>
            <TextField
              fullWidth
              label="Test Type"
              value={newTest.test_type}
              onChange={(e) => setNewTest({ ...newTest, test_type: e.target.value })}
              margin="normal"
            />
            <TextField
              fullWidth
              label="Result"
              value={newTest.result}
              onChange={(e) => setNewTest({ ...newTest, result: e.target.value })}
              margin="normal"
              multiline
              rows={4}
            />
            <TextField
              fullWidth
              type="date"
              label="Date"
              value={newTest.date}
              onChange={(e) => setNewTest({ ...newTest, date: e.target.value })}
              margin="normal"
              InputLabelProps={{ shrink: true }}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setAddTestOpen(false)}>Cancel</Button>
            <Button onClick={handleAddTest} variant="contained">
              Add Test Result
            </Button>
          </DialogActions>
        </Dialog>
      </Paper>
    </Container>
  );
}

export default DoctorDashboard;
