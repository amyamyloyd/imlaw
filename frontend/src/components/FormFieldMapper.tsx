import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Paper,
  List,
  ListItem,
  ListItemText,
  Chip,
  Grid,
  TextField,
  Divider,
  Alert,
  LinearProgress
} from '@mui/material';

interface FormField {
  field_name: string;
  form_id: string;
  tooltip: string;
  type: string;
  page: number;
  persona: string | null;
  domain: string | null;
  screen_label: string | null;
  value_info: any;
  mapped_collection_field: string | null;
  is_new_collection_field: boolean;
}

interface AvailableForm {
  id: string;
  name: string;
  display_name: string;
  has_saved_data: boolean;
}

export const FormFieldMapper: React.FC = () => {
  const [availableForms, setAvailableForms] = useState<AvailableForm[]>([]);
  const [selectedFormId, setSelectedFormId] = useState<string>('');
  const [fields, setFields] = useState<FormField[]>([]);
  const [collectionFields, setCollectionFields] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFieldIndex, setSelectedFieldIndex] = useState<number | null>(null);
  const [newCollectionField, setNewCollectionField] = useState('');

  useEffect(() => {
    fetchAvailableForms();
    fetchCollectionFields();
  }, []);

  const fetchAvailableForms = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/forms/available');
      const data = await response.json();
      setAvailableForms(data.forms);
    } catch (err) {
      setError('Failed to fetch available forms');
    }
  };

  const fetchCollectionFields = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/collection-fields');
      const data = await response.json();
      setCollectionFields(data.fields);
    } catch (err) {
      setError('Failed to fetch collection fields');
    }
  };

  const handleFormSelect = async (formId: string) => {
    setSelectedFormId(formId);
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`http://localhost:8000/api/forms/${formId}/analyze`, {
        method: 'POST'
      });
      
      if (!response.ok) {
        throw new Error('Failed to analyze form');
      }
      
      const data = await response.json();
      setFields(data.fields);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze form');
    } finally {
      setLoading(false);
    }
  };

  const saveFieldMapping = async (fieldIndex: number) => {
    const field = fields[fieldIndex];
    try {
      const response = await fetch(`http://localhost:8000/api/forms/${selectedFormId}/save-field`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(field),
      });
      
      if (!response.ok) {
        throw new Error('Failed to save field mapping');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save field mapping');
    }
  };

  const handleFieldChange = (fieldIndex: number, property: string, value: any) => {
    const updatedFields = [...fields];
    updatedFields[fieldIndex] = {
      ...updatedFields[fieldIndex],
      [property]: value
    };
    setFields(updatedFields);
  };

  const handleFieldBlur = (fieldIndex: number) => {
    // Auto-save on blur
    saveFieldMapping(fieldIndex);
  };

  const handleAddNewCollectionField = () => {
    if (newCollectionField.trim() && !collectionFields.includes(newCollectionField.trim()) && selectedFieldIndex !== null) {
      const newField = newCollectionField.trim();
      
      // Add to collection fields list
      setCollectionFields([...collectionFields, newField]);
      
      // Get the current field and update it
      const currentField = fields[selectedFieldIndex];
      const updatedField = {
        ...currentField,
        mapped_collection_field: newField,
        is_new_collection_field: true
      };
      
      // Update state
      const updatedFields = [...fields];
      updatedFields[selectedFieldIndex] = updatedField;
      setFields(updatedFields);
      
      // Save directly with the updated field data
      saveFieldMappingDirect(updatedField);
      
      setNewCollectionField('');
    }
  };

  const saveFieldMappingDirect = async (fieldData: FormField) => {
    try {
      const response = await fetch(`http://localhost:8000/api/forms/${selectedFormId}/save-field`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(fieldData),
      });
      
      if (!response.ok) {
        throw new Error('Failed to save field mapping');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save field mapping');
    }
  };

  const getPersonaOptions = () => [
    'applicant', 'beneficiary', 'family_member', 'preparer', 'attorney', 
    'interpreter', 'employer', 'physician', 'sponsor'
  ];

  const getDomainOptions = () => [
    'personal', 'medical', 'criminal', 'immigration', 'office'
  ];

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Form Field Mapper
      </Typography>
      
      <Paper sx={{ p: 3, mb: 3 }}>
        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>Select Form</InputLabel>
          <Select
            value={selectedFormId}
            label="Select Form"
            onChange={(e) => handleFormSelect(e.target.value)}
          >
            {availableForms.map((form) => (
              <MenuItem key={form.id} value={form.id}>
                {form.display_name} {form.has_saved_data && '(Has saved data)'}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        
        {selectedFormId && (
          <Typography variant="body2" color="text.secondary">
            Selected: {availableForms.find(f => f.id === selectedFormId)?.display_name}
          </Typography>
        )}
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {loading && <LinearProgress sx={{ mb: 3 }} />}

      {fields.length > 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, height: '70vh', overflow: 'auto' }}>
              <Typography variant="h6" gutterBottom>
                Form Fields ({fields.length})
              </Typography>
              <List>
                {fields.map((field, index) => (
                  <ListItem
                    key={field.field_name}
                    button
                    selected={selectedFieldIndex === index}
                    onClick={() => setSelectedFieldIndex(index)}
                    sx={{ 
                      border: '1px solid #e0e0e0',
                      mb: 1,
                      borderRadius: 1,
                      bgcolor: selectedFieldIndex === index ? 'action.selected' : 'background.paper'
                    }}
                  >
                    <ListItemText
                      primary={field.field_name}
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            {field.tooltip || 'No tooltip'}
                          </Typography>
                          <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                            {field.persona && (
                              <Chip label={`Persona: ${field.persona}`} size="small" color="primary" />
                            )}
                            {field.domain && (
                              <Chip label={`Domain: ${field.domain}`} size="small" color="secondary" />
                            )}
                            {field.mapped_collection_field && (
                              <Chip label={`Mapped: ${field.mapped_collection_field}`} size="small" color="success" />
                            )}
                          </Box>
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            {selectedFieldIndex !== null && (
              <Paper sx={{ p: 2, height: '70vh', overflow: 'auto' }}>
                <Typography variant="h6" gutterBottom>
                  Edit Field Mapping
                </Typography>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2">Field Name:</Typography>
                  <Typography variant="body2">{fields[selectedFieldIndex].field_name}</Typography>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2">Tooltip:</Typography>
                  <Typography variant="body2">{fields[selectedFieldIndex].tooltip || 'No tooltip'}</Typography>
                </Box>

                <Divider sx={{ my: 2 }} />

                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Persona</InputLabel>
                  <Select
                    value={fields[selectedFieldIndex].persona || ''}
                    label="Persona"
                    onChange={(e) => handleFieldChange(selectedFieldIndex, 'persona', e.target.value)}
                    onBlur={() => handleFieldBlur(selectedFieldIndex)}
                  >
                    <MenuItem value="">None</MenuItem>
                    {getPersonaOptions().map((option) => (
                      <MenuItem key={option} value={option}>
                        {option}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Domain</InputLabel>
                  <Select
                    value={fields[selectedFieldIndex].domain || ''}
                    label="Domain"
                    onChange={(e) => handleFieldChange(selectedFieldIndex, 'domain', e.target.value)}
                    onBlur={() => handleFieldBlur(selectedFieldIndex)}
                  >
                    <MenuItem value="">None</MenuItem>
                    {getDomainOptions().map((option) => (
                      <MenuItem key={option} value={option}>
                        {option}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Collection Field</InputLabel>
                  <Select
                    value={fields[selectedFieldIndex].mapped_collection_field || ''}
                    label="Collection Field"
                    onChange={(e) => handleFieldChange(selectedFieldIndex, 'mapped_collection_field', e.target.value)}
                    onBlur={() => handleFieldBlur(selectedFieldIndex)}
                  >
                    <MenuItem value="">None</MenuItem>
                    {collectionFields.map((field) => (
                      <MenuItem key={field} value={field}>
                        {field}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                  <TextField
                    size="small"
                    label="New Collection Field"
                    value={newCollectionField}
                    onChange={(e) => setNewCollectionField(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleAddNewCollectionField()}
                  />
                  <Button
                    variant="outlined"
                    onClick={handleAddNewCollectionField}
                  >
                    Add
                  </Button>
                </Box>
              </Paper>
            )}
          </Grid>
        </Grid>
      )}
    </Box>
  );
}; 