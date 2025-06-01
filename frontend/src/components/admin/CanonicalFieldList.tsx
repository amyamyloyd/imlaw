import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Tooltip,
  Typography,
} from '@mui/material';
import { Edit as EditIcon, Delete as DeleteIcon, Add as AddIcon } from '@mui/icons-material';
import { DataType } from '../../types/canonical-field';

interface CanonicalField {
  field_name: string;
  display_name: string;
  description?: string;
  data_type: DataType;
  category?: string;
  required: boolean;
  form_mappings: Array<{
    form_type: string;
    form_version: string;
    field_id: string;
  }>;
  usage_stats: {
    total_uses: number;
    error_count: number;
  };
}

interface CanonicalFieldListProps {
  onEdit: (field: CanonicalField) => void;
  onDelete: (fieldName: string) => void;
  onAdd: () => void;
}

export const CanonicalFieldList: React.FC<CanonicalFieldListProps> = ({
  onEdit,
  onDelete,
  onAdd,
}) => {
  const [fields, setFields] = useState<CanonicalField[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchText, setSearchText] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [dataTypeFilter, setDataTypeFilter] = useState<string>('all');

  useEffect(() => {
    fetchFields();
  }, [page, rowsPerPage, categoryFilter, dataTypeFilter]);

  const fetchFields = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/canonical-fields?' + new URLSearchParams({
        page: (page + 1).toString(),
        page_size: rowsPerPage.toString(),
        ...(categoryFilter !== 'all' && { category: categoryFilter }),
        ...(dataTypeFilter !== 'all' && { data_type: dataTypeFilter }),
      }));
      
      if (!response.ok) {
        throw new Error('Failed to fetch fields');
      }
      
      const data = await response.json();
      setFields(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const filteredFields = fields.filter(field => 
    field.field_name.toLowerCase().includes(searchText.toLowerCase()) ||
    field.display_name.toLowerCase().includes(searchText.toLowerCase())
  );

  if (error) {
    return (
      <Box sx={{ p: 2 }}>
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ display: 'flex', gap: 2, mb: 2, alignItems: 'center' }}>
        <TextField
          label="Search fields"
          variant="outlined"
          size="small"
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          sx={{ flexGrow: 1 }}
        />
        
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Category</InputLabel>
          <Select
            value={categoryFilter}
            label="Category"
            onChange={(e) => setCategoryFilter(e.target.value)}
          >
            <MenuItem value="all">All</MenuItem>
            <MenuItem value="personal">Personal</MenuItem>
            <MenuItem value="address">Address</MenuItem>
            <MenuItem value="contact">Contact</MenuItem>
          </Select>
        </FormControl>
        
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Data Type</InputLabel>
          <Select
            value={dataTypeFilter}
            label="Data Type"
            onChange={(e) => setDataTypeFilter(e.target.value)}
          >
            <MenuItem value="all">All</MenuItem>
            <MenuItem value="string">String</MenuItem>
            <MenuItem value="number">Number</MenuItem>
            <MenuItem value="date">Date</MenuItem>
            <MenuItem value="boolean">Boolean</MenuItem>
          </Select>
        </FormControl>
        
        <Tooltip title="Add new field">
          <IconButton onClick={onAdd} color="primary">
            <AddIcon />
          </IconButton>
        </Tooltip>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Field Name</TableCell>
              <TableCell>Display Name</TableCell>
              <TableCell>Data Type</TableCell>
              <TableCell>Category</TableCell>
              <TableCell>Required</TableCell>
              <TableCell>Mappings</TableCell>
              <TableCell>Usage</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={8} align="center">Loading...</TableCell>
              </TableRow>
            ) : filteredFields.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center">No fields found</TableCell>
              </TableRow>
            ) : (
              filteredFields.map((field) => (
                <TableRow key={field.field_name}>
                  <TableCell>{field.field_name}</TableCell>
                  <TableCell>{field.display_name}</TableCell>
                  <TableCell>{field.data_type}</TableCell>
                  <TableCell>{field.category || '-'}</TableCell>
                  <TableCell>{field.required ? 'Yes' : 'No'}</TableCell>
                  <TableCell>{field.form_mappings.length}</TableCell>
                  <TableCell>
                    {field.usage_stats.total_uses} uses
                    {field.usage_stats.error_count > 0 && (
                      <Typography component="span" color="error">
                        {` (${field.usage_stats.error_count} errors)`}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Tooltip title="Edit field">
                      <IconButton onClick={() => onEdit(field)} size="small">
                        <EditIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete field">
                      <IconButton 
                        onClick={() => onDelete(field.field_name)}
                        size="small"
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={fields.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </TableContainer>
    </Box>
  );
}; 