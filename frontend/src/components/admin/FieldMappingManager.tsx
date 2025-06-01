import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Check as CheckIcon,
} from '@mui/icons-material';
import { FormFieldMapping } from '../../types/canonical-field';

interface FieldMappingManagerProps {
  canonicalFieldName: string;
  mappings: FormFieldMapping[];
  onMappingsChange: (mappings: FormFieldMapping[]) => void;
}

interface MappingSuggestion {
  form_type: string;
  form_version: string;
  field_id: string;
  confidence: number;
  reason: string;
}

export const FieldMappingManager: React.FC<FieldMappingManagerProps> = ({
  canonicalFieldName,
  mappings,
  onMappingsChange,
}) => {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [suggestions, setSuggestions] = useState<MappingSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [newMapping, setNewMapping] = useState<Partial<FormFieldMapping>>({
    form_type: '',
    form_version: '',
    field_id: '',
    mapping_type: 'direct',
  });
  const [availableForms, setAvailableForms] = useState<Array<{
    type: string;
    versions: string[];
  }>>([]);

  useEffect(() => {
    fetchAvailableForms();
    if (canonicalFieldName) {
      fetchMappingSuggestions();
    }
  }, [canonicalFieldName]);

  const fetchAvailableForms = async () => {
    try {
      const response = await fetch('/api/forms/available');
      if (!response.ok) throw new Error('Failed to fetch available forms');
      const data = await response.json();
      setAvailableForms(data);
    } catch (error) {
      console.error('Error fetching available forms:', error);
    }
  };

  const fetchMappingSuggestions = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/field-mappings/suggestions/${canonicalFieldName}`);
      if (!response.ok) throw new Error('Failed to fetch mapping suggestions');
      const data = await response.json();
      setSuggestions(data);
    } catch (error) {
      console.error('Error fetching mapping suggestions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddMapping = async () => {
    if (!newMapping.form_type || !newMapping.form_version || !newMapping.field_id) {
      return;
    }

    const mappingToAdd: FormFieldMapping = {
      ...newMapping as FormFieldMapping,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    onMappingsChange([...mappings, mappingToAdd]);
    setNewMapping({
      form_type: '',
      form_version: '',
      field_id: '',
      mapping_type: 'direct',
    });
    setDialogOpen(false);
  };

  const handleRemoveMapping = (index: number) => {
    const updatedMappings = mappings.filter((_, i) => i !== index);
    onMappingsChange(updatedMappings);
  };

  const handleAcceptSuggestion = (suggestion: MappingSuggestion) => {
    const newMappingFromSuggestion: FormFieldMapping = {
      form_type: suggestion.form_type,
      form_version: suggestion.form_version,
      field_id: suggestion.field_id,
      mapping_type: 'direct',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    onMappingsChange([...mappings, newMappingFromSuggestion]);
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6">Field Mappings</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setDialogOpen(true)}
        >
          Add Mapping
        </Button>
      </Box>

      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Form Type</TableCell>
              <TableCell>Version</TableCell>
              <TableCell>Field ID</TableCell>
              <TableCell>Mapping Type</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {mappings.map((mapping, index) => (
              <TableRow key={`${mapping.form_type}-${mapping.field_id}-${index}`}>
                <TableCell>{mapping.form_type}</TableCell>
                <TableCell>{mapping.form_version}</TableCell>
                <TableCell>{mapping.field_id}</TableCell>
                <TableCell>
                  <Chip
                    label={mapping.mapping_type}
                    color={mapping.mapping_type === 'direct' ? 'primary' : 'secondary'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => handleRemoveMapping(index)}
                  >
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {suggestions.length > 0 && (
        <Box sx={{ mt: 4 }}>
          <Typography variant="h6" gutterBottom>
            Suggested Mappings
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Form Type</TableCell>
                  <TableCell>Version</TableCell>
                  <TableCell>Field ID</TableCell>
                  <TableCell>Confidence</TableCell>
                  <TableCell>Reason</TableCell>
                  <TableCell>Action</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {suggestions.map((suggestion, index) => (
                  <TableRow key={index}>
                    <TableCell>{suggestion.form_type}</TableCell>
                    <TableCell>{suggestion.form_version}</TableCell>
                    <TableCell>{suggestion.field_id}</TableCell>
                    <TableCell>
                      <Chip
                        label={`${Math.round(suggestion.confidence * 100)}%`}
                        color={suggestion.confidence > 0.8 ? 'success' : 'warning'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{suggestion.reason}</TableCell>
                    <TableCell>
                      <Tooltip title="Accept suggestion">
                        <IconButton
                          size="small"
                          color="success"
                          onClick={() => handleAcceptSuggestion(suggestion)}
                        >
                          <CheckIcon />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
        <DialogTitle>Add Field Mapping</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ pt: 2 }}>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Form Type</InputLabel>
                <Select
                  value={newMapping.form_type}
                  label="Form Type"
                  onChange={(e) => setNewMapping({
                    ...newMapping,
                    form_type: e.target.value as string,
                    form_version: '', // Reset version when form type changes
                  })}
                >
                  {availableForms.map(form => (
                    <MenuItem key={form.type} value={form.type}>
                      {form.type}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Form Version</InputLabel>
                <Select
                  value={newMapping.form_version}
                  label="Form Version"
                  onChange={(e) => setNewMapping({
                    ...newMapping,
                    form_version: e.target.value as string,
                  })}
                  disabled={!newMapping.form_type}
                >
                  {availableForms
                    .find(f => f.type === newMapping.form_type)
                    ?.versions.map(version => (
                      <MenuItem key={version} value={version}>
                        {version}
                      </MenuItem>
                    ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Field ID"
                value={newMapping.field_id}
                onChange={(e) => setNewMapping({
                  ...newMapping,
                  field_id: e.target.value,
                })}
              />
            </Grid>

            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Mapping Type</InputLabel>
                <Select
                  value={newMapping.mapping_type}
                  label="Mapping Type"
                  onChange={(e) => setNewMapping({
                    ...newMapping,
                    mapping_type: e.target.value as 'direct' | 'transform' | 'composite',
                  })}
                >
                  <MenuItem value="direct">Direct</MenuItem>
                  <MenuItem value="transform">Transform</MenuItem>
                  <MenuItem value="composite">Composite</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            {newMapping.mapping_type === 'transform' && (
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Transform Logic"
                  multiline
                  rows={3}
                  value={newMapping.transform_logic || ''}
                  onChange={(e) => setNewMapping({
                    ...newMapping,
                    transform_logic: e.target.value,
                  })}
                />
              </Grid>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleAddMapping} color="primary">
            Add Mapping
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
}; 