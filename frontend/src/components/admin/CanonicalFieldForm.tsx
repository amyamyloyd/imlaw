import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Typography,
  Paper,
  Chip,
  IconButton,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { 
  CanonicalField, 
  DataType, 
  ValidationRule,
  FormFieldMapping 
} from '../../types/canonical-field';

interface CanonicalFieldFormProps {
  field?: CanonicalField;
  onSubmit: (field: CanonicalField) => void;
  onCancel: () => void;
}

const INITIAL_FIELD: CanonicalField = {
  field_name: '',
  display_name: '',
  description: '',
  data_type: DataType.STRING,
  validation_rules: [],
  form_mappings: [],
  required: false,
  dependencies: [],
  aliases: [],
  source_priority: [],
  validation_history: [],
  usage_stats: {
    total_uses: 0,
    form_usage: {},
    error_count: 0
  },
  metadata: {},
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString()
};

export const CanonicalFieldForm: React.FC<CanonicalFieldFormProps> = ({
  field,
  onSubmit,
  onCancel
}) => {
  const [formData, setFormData] = useState<CanonicalField>(field || INITIAL_FIELD);
  const [validationDialogOpen, setValidationDialogOpen] = useState(false);
  const [newValidationRule, setNewValidationRule] = useState<ValidationRule>({
    rule_type: '',
    parameters: {},
    error_message: ''
  });
  const [newAlias, setNewAlias] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | { name?: string; value: unknown }>
  ) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name as string]: value
    }));
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.field_name.trim()) {
      newErrors.field_name = 'Field name is required';
    }
    if (!formData.display_name.trim()) {
      newErrors.display_name = 'Display name is required';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    const updatedField = {
      ...formData,
      updated_at: new Date().toISOString()
    };
    
    onSubmit(updatedField);
  };

  const handleAddValidationRule = () => {
    if (newValidationRule.rule_type && Object.keys(newValidationRule.parameters).length > 0) {
      setFormData(prev => ({
        ...prev,
        validation_rules: [...prev.validation_rules, newValidationRule]
      }));
      setNewValidationRule({
        rule_type: '',
        parameters: {},
        error_message: ''
      });
      setValidationDialogOpen(false);
    }
  };

  const handleRemoveValidationRule = (index: number) => {
    setFormData(prev => ({
      ...prev,
      validation_rules: prev.validation_rules.filter((_, i) => i !== index)
    }));
  };

  const handleAddAlias = () => {
    if (newAlias.trim() && !formData.aliases.includes(newAlias.trim())) {
      setFormData(prev => ({
        ...prev,
        aliases: [...prev.aliases, newAlias.trim()]
      }));
      setNewAlias('');
    }
  };

  const handleRemoveAlias = (alias: string) => {
    setFormData(prev => ({
      ...prev,
      aliases: prev.aliases.filter(a => a !== alias)
    }));
  };

  return (
    <Paper sx={{ p: 3 }}>
      <form onSubmit={handleSubmit}>
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              {field ? 'Edit Canonical Field' : 'Create New Canonical Field'}
            </Typography>
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Field Name"
              name="field_name"
              value={formData.field_name}
              onChange={handleInputChange}
              error={!!errors.field_name}
              helperText={errors.field_name}
              required
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Display Name"
              name="display_name"
              value={formData.display_name}
              onChange={handleInputChange}
              error={!!errors.display_name}
              helperText={errors.display_name}
              required
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Description"
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              multiline
              rows={3}
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Data Type</InputLabel>
              <Select
                name="data_type"
                value={formData.data_type}
                onChange={handleInputChange}
                label="Data Type"
                required
              >
                {Object.values(DataType).map(type => (
                  <MenuItem key={type} value={type}>
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Category"
              name="category"
              value={formData.category}
              onChange={handleInputChange}
            />
          </Grid>

          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={formData.required}
                  onChange={(e) => handleInputChange({
                    target: { name: 'required', value: e.target.checked }
                  } as any)}
                  name="required"
                />
              }
              label="Required Field"
            />
          </Grid>

          <Grid item xs={12}>
            <Typography variant="subtitle1" gutterBottom>
              Aliases
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
              <TextField
                size="small"
                label="New Alias"
                value={newAlias}
                onChange={(e) => setNewAlias(e.target.value)}
              />
              <Button
                variant="outlined"
                onClick={handleAddAlias}
                startIcon={<AddIcon />}
              >
                Add
              </Button>
            </Box>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {formData.aliases.map((alias) => (
                <Chip
                  key={alias}
                  label={alias}
                  onDelete={() => handleRemoveAlias(alias)}
                />
              ))}
            </Box>
          </Grid>

          <Grid item xs={12}>
            <Typography variant="subtitle1" gutterBottom>
              Validation Rules
            </Typography>
            <Button
              variant="outlined"
              onClick={() => setValidationDialogOpen(true)}
              startIcon={<AddIcon />}
            >
              Add Validation Rule
            </Button>
            <Box sx={{ mt: 2 }}>
              {formData.validation_rules.map((rule, index) => (
                <Box
                  key={index}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    mb: 1,
                    p: 1,
                    border: '1px solid #e0e0e0',
                    borderRadius: 1
                  }}
                >
                  <Typography>
                    {rule.rule_type}
                    {rule.error_message && ` - ${rule.error_message}`}
                  </Typography>
                  <IconButton
                    size="small"
                    onClick={() => handleRemoveValidationRule(index)}
                  >
                    <DeleteIcon />
                  </IconButton>
                </Box>
              ))}
            </Box>
          </Grid>

          <Grid item xs={12}>
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
              <Button variant="outlined" onClick={onCancel}>
                Cancel
              </Button>
              <Button variant="contained" color="primary" type="submit">
                {field ? 'Update Field' : 'Create Field'}
              </Button>
            </Box>
          </Grid>
        </Grid>
      </form>

      <Dialog
        open={validationDialogOpen}
        onClose={() => setValidationDialogOpen(false)}
      >
        <DialogTitle>Add Validation Rule</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Rule Type</InputLabel>
              <Select
                value={newValidationRule.rule_type}
                onChange={(e) => setNewValidationRule(prev => ({
                  ...prev,
                  rule_type: e.target.value as string
                }))}
                label="Rule Type"
              >
                <MenuItem value="length">Length</MenuItem>
                <MenuItem value="regex">Regex</MenuItem>
                <MenuItem value="range">Range</MenuItem>
                <MenuItem value="enum">Enumeration</MenuItem>
                <MenuItem value="custom">Custom</MenuItem>
              </Select>
            </FormControl>

            <TextField
              fullWidth
              label="Error Message"
              value={newValidationRule.error_message}
              onChange={(e) => setNewValidationRule(prev => ({
                ...prev,
                error_message: e.target.value
              }))}
              sx={{ mb: 2 }}
            />

            {/* Add specific parameter fields based on rule_type */}
            {newValidationRule.rule_type === 'length' && (
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Min Length"
                    onChange={(e) => setNewValidationRule(prev => ({
                      ...prev,
                      parameters: {
                        ...prev.parameters,
                        min: parseInt(e.target.value)
                      }
                    }))}
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Max Length"
                    onChange={(e) => setNewValidationRule(prev => ({
                      ...prev,
                      parameters: {
                        ...prev.parameters,
                        max: parseInt(e.target.value)
                      }
                    }))}
                  />
                </Grid>
              </Grid>
            )}

            {/* Add other rule type specific parameter fields */}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setValidationDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleAddValidationRule} color="primary">
            Add Rule
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
}; 