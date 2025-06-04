import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from 'react-resizable-panels';
import { 
    Box, 
    Typography, 
    List, 
    ListItem, 
    ListItemText, 
    Button, 
    Paper, 
    Chip,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    Alert,
    LinearProgress,
    TextField
} from '@mui/material';
import { 
    CloudUpload, 
    Save, 
    Download, 
    Visibility 
} from '@mui/icons-material';

// Types
interface FormField {
    name: string;
    type: string;
    tooltip: string;
    page: number;
    persona: string | null;
    domain: string | null;
    screen_label: string | null;
    value_info: any;
    hierarchy: any;
}

interface FieldMapping {
    formFieldName: string;
    persona: string;
    domain: string;
    collectionFieldName: string;
}

// Constants from your existing analyzer
const PERSONAS = [
    'applicant', 'beneficiary', 'family_member', 'preparer', 
    'attorney', 'interpreter', 'employer', 'physician', 'sponsor'
];

const DOMAINS = [
    'personal', 'medical', 'criminal', 'immigration', 'office'
];

const COLLECTION_FIELDS = [
    'Given Name', 'Middle Name', 'Family Name', 'Alien Number', 'SSN',
    'Passport', 'TravelDoc', 'Date of Birth', 'Port of Entry', 'City of Entry',
    'Country of Birth', 'Email address', 'Employer Name', 'DayTime Phone Number',
    'Mobile Number', 'Apt', 'Str', 'Flr Number', 'Street Address', 'City',
    'State', 'Country', 'Nationality', 'Language'
];

const PDFFieldMapper: React.FC = () => {
    const [fields, setFields] = useState<FormField[]>([]);
    const [selectedField, setSelectedField] = useState<string | null>(null);
    const [fieldMappings, setFieldMappings] = useState<Record<string, FieldMapping>>({});
    const [pdfUrl, setPdfUrl] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [newCollectionFields, setNewCollectionFields] = useState<string[]>([]);
    
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Load progress from localStorage on component mount
    useEffect(() => {
        const savedProgress = localStorage.getItem('pdf_field_mapping_progress');
        if (savedProgress) {
            try {
                const progress = JSON.parse(savedProgress);
                setFieldMappings(progress.fieldMappings || {});
                setNewCollectionFields(progress.newCollectionFields || []);
            } catch (e) {
                console.error('Error loading progress from localStorage:', e);
            }
        }
    }, []);

    // Save progress to localStorage whenever mappings change
    useEffect(() => {
        const progress = {
            fieldMappings,
            newCollectionFields,
            timestamp: new Date().toISOString()
        };
        localStorage.setItem('pdf_field_mapping_progress', JSON.stringify(progress));
    }, [fieldMappings, newCollectionFields]);

    const onDrop = useCallback(async (acceptedFiles: File[]) => {
        const file = acceptedFiles[0];
        if (!file) return;

        setLoading(true);
        setError(null);

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/api/pdf/upload', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error('Upload failed');
            }

            const result = await response.json();
            setFields(result.fields);
            
            // Create PDF URL for viewing
            const pdfObjectUrl = URL.createObjectURL(file);
            setPdfUrl(pdfObjectUrl);

        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
        } finally {
            setLoading(false);
        }
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'application/pdf': ['.pdf']
        },
        multiple: false
    });

    const updateFieldMapping = (fieldName: string, key: keyof FieldMapping, value: string) => {
        setFieldMappings(prev => ({
            ...prev,
            [fieldName]: {
                ...prev[fieldName],
                formFieldName: fieldName,
                [key]: value
            } as FieldMapping
        }));
    };

    const addNewCollectionField = (newField: string) => {
        if (newField && !COLLECTION_FIELDS.includes(newField) && !newCollectionFields.includes(newField)) {
            setNewCollectionFields(prev => [...prev, newField]);
        }
    };

    const exportMappings = () => {
        const exportData = {
            filename: fields.length > 0 ? `mapping_${Date.now()}.json` : 'no_file',
            timestamp: new Date().toISOString(),
            totalFields: fields.length,
            mappedFields: Object.keys(fieldMappings).length,
            fieldMappings,
            newCollectionFields,
            fields
        };

        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `field_mapping_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
    };

    const saveProgress = async () => {
        try {
            const progressData = {
                fieldMappings,
                newCollectionFields,
                fields,
                timestamp: new Date().toISOString()
            };

            const response = await fetch('/api/pdf/save-progress', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(progressData)
            });

            if (response.ok) {
                alert('Progress saved to server successfully!');
            }
        } catch (err) {
            console.error('Error saving progress:', err);
            alert('Error saving progress to server');
        }
    };

    const allCollectionFields = [...COLLECTION_FIELDS, ...newCollectionFields];

    return (
        <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
            <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
                <Typography variant="h4" component="h1" gutterBottom>
                    PDF Field Mapper
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                    <Button 
                        variant="contained" 
                        startIcon={<CloudUpload />}
                        onClick={() => fileInputRef.current?.click()}
                    >
                        Upload PDF
                    </Button>
                    <Button 
                        variant="outlined" 
                        startIcon={<Save />}
                        onClick={saveProgress}
                        disabled={fields.length === 0}
                    >
                        Save Progress
                    </Button>
                    <Button 
                        variant="outlined" 
                        startIcon={<Download />}
                        onClick={exportMappings}
                        disabled={fields.length === 0}
                    >
                        Export Mappings
                    </Button>
                </Box>
                <input 
                    ref={fileInputRef}
                    {...getInputProps()}
                    style={{ display: 'none' }}
                />
            </Box>

            {loading && <LinearProgress />}
            {error && <Alert severity="error" sx={{ m: 2 }}>{error}</Alert>}

            <Box sx={{ flex: 1, overflow: 'hidden' }}>
                {fields.length === 0 ? (
                    <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <Paper 
                            {...getRootProps()} 
                            sx={{ 
                                p: 4, 
                                border: 2, 
                                borderStyle: 'dashed', 
                                borderColor: isDragActive ? 'primary.main' : 'grey.300',
                                cursor: 'pointer',
                                textAlign: 'center'
                            }}
                        >
                            <CloudUpload sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
                            <Typography variant="h6" gutterBottom>
                                {isDragActive ? 'Drop PDF here' : 'Drag & drop a PDF file here, or click to select'}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                                Upload a government PDF form to extract and map fields
                            </Typography>
                        </Paper>
                    </Box>
                ) : (
                    <ResizablePanelGroup direction="horizontal">
                        <ResizablePanel defaultSize={40} minSize={30}>
                            <Box sx={{ height: '100%', overflow: 'auto', p: 2 }}>
                                <Typography variant="h6" gutterBottom>
                                    Form Fields ({fields.length})
                                </Typography>
                                <List>
                                    {fields.map((field) => (
                                        <ListItem 
                                            key={field.name}
                                            onClick={() => setSelectedField(field.name)}
                                            sx={{ 
                                                cursor: 'pointer',
                                                backgroundColor: selectedField === field.name ? 'action.selected' : 'transparent',
                                                '&:hover': { backgroundColor: 'action.hover' },
                                                mb: 1,
                                                borderRadius: 1
                                            }}
                                        >
                                            <ListItemText
                                                primary={field.name}
                                                secondary={
                                                    <Box sx={{ mt: 1 }}>
                                                        <Typography variant="caption" component="div">
                                                            {field.tooltip && `"${field.tooltip.substring(0, 100)}..."`}
                                                        </Typography>
                                                        <Box sx={{ display: 'flex', gap: 1, mt: 1, flexWrap: 'wrap' }}>
                                                            {field.persona && <Chip label={field.persona} size="small" color="primary" />}
                                                            {field.domain && <Chip label={field.domain} size="small" color="secondary" />}
                                                        </Box>
                                                        
                                                        {/* Mapping Controls */}
                                                        <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 1 }}>
                                                            <FormControl size="small" fullWidth>
                                                                <InputLabel>Persona</InputLabel>
                                                                <Select
                                                                    value={fieldMappings[field.name]?.persona || field.persona || ''}
                                                                    onChange={(e) => updateFieldMapping(field.name, 'persona', e.target.value)}
                                                                    label="Persona"
                                                                >
                                                                    {PERSONAS.map(persona => (
                                                                        <MenuItem key={persona} value={persona}>{persona}</MenuItem>
                                                                    ))}
                                                                </Select>
                                                            </FormControl>
                                                            
                                                            <FormControl size="small" fullWidth>
                                                                <InputLabel>Domain</InputLabel>
                                                                <Select
                                                                    value={fieldMappings[field.name]?.domain || field.domain || ''}
                                                                    onChange={(e) => updateFieldMapping(field.name, 'domain', e.target.value)}
                                                                    label="Domain"
                                                                >
                                                                    {DOMAINS.map(domain => (
                                                                        <MenuItem key={domain} value={domain}>{domain}</MenuItem>
                                                                    ))}
                                                                </Select>
                                                            </FormControl>
                                                            
                                                            <FormControl size="small" fullWidth>
                                                                <InputLabel>Collection Field</InputLabel>
                                                                <Select
                                                                    value={fieldMappings[field.name]?.collectionFieldName || ''}
                                                                    onChange={(e) => updateFieldMapping(field.name, 'collectionFieldName', e.target.value)}
                                                                    label="Collection Field"
                                                                >
                                                                    {allCollectionFields.map(collectionField => (
                                                                        <MenuItem key={collectionField} value={collectionField}>
                                                                            {collectionField}
                                                                        </MenuItem>
                                                                    ))}
                                                                    <MenuItem value="__new__">+ Add New Field</MenuItem>
                                                                </Select>
                                                            </FormControl>
                                                            
                                                            {fieldMappings[field.name]?.collectionFieldName === '__new__' && (
                                                                <TextField
                                                                    size="small"
                                                                    label="New Collection Field Name"
                                                                    onKeyPress={(e) => {
                                                                        if (e.key === 'Enter') {
                                                                            const newField = (e.target as HTMLInputElement).value.trim();
                                                                            if (newField) {
                                                                                addNewCollectionField(newField);
                                                                                updateFieldMapping(field.name, 'collectionFieldName', newField);
                                                                                (e.target as HTMLInputElement).value = '';
                                                                            }
                                                                        }
                                                                    }}
                                                                />
                                                            )}
                                                        </Box>
                                                    </Box>
                                                }
                                            />
                                        </ListItem>
                                    ))}
                                </List>
                            </Box>
                        </ResizablePanel>
                        
                        <ResizableHandle />
                        
                        <ResizablePanel defaultSize={60} minSize={40}>
                            <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                                <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
                                    <Typography variant="h6">
                                        PDF Preview {selectedField && `- ${selectedField}`}
                                    </Typography>
                                </Box>
                                <Box sx={{ flex: 1, overflow: 'auto', bgcolor: 'grey.100' }}>
                                    {pdfUrl ? (
                                        <iframe
                                            src={pdfUrl}
                                            style={{ width: '100%', height: '100%', border: 'none' }}
                                            title="PDF Preview"
                                        />
                                    ) : (
                                        <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                            <Typography variant="body1" color="text.secondary">
                                                PDF preview will appear here
                                            </Typography>
                                        </Box>
                                    )}
                                </Box>
                            </Box>
                        </ResizablePanel>
                    </ResizablePanelGroup>
                )}
            </Box>
        </Box>
    );
};

export default PDFFieldMapper; 