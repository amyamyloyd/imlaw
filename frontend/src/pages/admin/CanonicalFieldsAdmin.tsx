import React, { useState } from 'react';
import {
  Box,
  Container,
  Dialog,
  DialogContent,
  Snackbar,
  Alert,
} from '@mui/material';
import { CanonicalFieldList } from '../../components/admin/CanonicalFieldList';
import { CanonicalFieldForm } from '../../components/admin/CanonicalFieldForm';
import { FieldMappingManager } from '../../components/admin/FieldMappingManager';
import { CanonicalField } from '../../types/canonical-field';

export const CanonicalFieldsAdmin: React.FC = () => {
  const [formDialogOpen, setFormDialogOpen] = useState(false);
  const [mappingDialogOpen, setMappingDialogOpen] = useState(false);
  const [selectedField, setSelectedField] = useState<CanonicalField | null>(null);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error';
  }>({
    open: false,
    message: '',
    severity: 'success',
  });

  const handleAddField = () => {
    setSelectedField(null);
    setFormDialogOpen(true);
  };

  const handleEditField = (field: CanonicalField) => {
    setSelectedField(field);
    setFormDialogOpen(true);
  };

  const handleDeleteField = async (fieldName: string) => {
    try {
      const response = await fetch(`/api/canonical-fields/${fieldName}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete field');
      }

      setSnackbar({
        open: true,
        message: 'Field deleted successfully',
        severity: 'success',
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: error instanceof Error ? error.message : 'Failed to delete field',
        severity: 'error',
      });
    }
  };

  const handleSubmitField = async (field: CanonicalField) => {
    try {
      const method = selectedField ? 'PUT' : 'POST';
      const url = selectedField
        ? `/api/canonical-fields/${selectedField.field_name}`
        : '/api/canonical-fields';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(field),
      });

      if (!response.ok) {
        throw new Error('Failed to save field');
      }

      setSnackbar({
        open: true,
        message: `Field ${selectedField ? 'updated' : 'created'} successfully`,
        severity: 'success',
      });
      setFormDialogOpen(false);
    } catch (error) {
      setSnackbar({
        open: true,
        message: error instanceof Error ? error.message : 'Failed to save field',
        severity: 'error',
      });
    }
  };

  const handleManageMappings = (field: CanonicalField) => {
    setSelectedField(field);
    setMappingDialogOpen(true);
  };

  const handleMappingsChange = async (mappings: CanonicalField['form_mappings']) => {
    if (!selectedField) return;

    try {
      const response = await fetch(`/api/canonical-fields/${selectedField.field_name}/mappings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ mappings }),
      });

      if (!response.ok) {
        throw new Error('Failed to update mappings');
      }

      setSnackbar({
        open: true,
        message: 'Mappings updated successfully',
        severity: 'success',
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: error instanceof Error ? error.message : 'Failed to update mappings',
        severity: 'error',
      });
    }
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ py: 4 }}>
        <CanonicalFieldList
          onAdd={handleAddField}
          onEdit={handleEditField}
          onDelete={handleDeleteField}
        />

        <Dialog
          open={formDialogOpen}
          onClose={() => setFormDialogOpen(false)}
          maxWidth="md"
          fullWidth
        >
          <DialogContent>
            <CanonicalFieldForm
              field={selectedField || undefined}
              onSubmit={handleSubmitField}
              onCancel={() => setFormDialogOpen(false)}
            />
          </DialogContent>
        </Dialog>

        <Dialog
          open={mappingDialogOpen}
          onClose={() => setMappingDialogOpen(false)}
          maxWidth="lg"
          fullWidth
        >
          <DialogContent>
            {selectedField && (
              <FieldMappingManager
                canonicalFieldName={selectedField.field_name}
                mappings={selectedField.form_mappings}
                onMappingsChange={handleMappingsChange}
              />
            )}
          </DialogContent>
        </Dialog>

        <Snackbar
          open={snackbar.open}
          autoHideDuration={6000}
          onClose={() => setSnackbar({ ...snackbar, open: false })}
        >
          <Alert
            onClose={() => setSnackbar({ ...snackbar, open: false })}
            severity={snackbar.severity}
            sx={{ width: '100%' }}
          >
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Box>
    </Container>
  );
}; 