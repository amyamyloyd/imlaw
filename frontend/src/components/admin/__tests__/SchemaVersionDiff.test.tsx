import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { message } from 'antd';
import SchemaVersionDiff from '../SchemaVersionDiff';

// Mock fetch
global.fetch = jest.fn();

// Mock antd message
jest.mock('antd', () => ({
  ...jest.requireActual('antd'),
  message: {
    error: jest.fn(),
  },
}));

describe('SchemaVersionDiff', () => {
  const mockDiffData = {
    from_version: '1.0.0',
    to_version: '1.1.0',
    timestamp: '2024-01-01T00:00:00Z',
    changes: [
      {
        field_id: 'name',
        field_name: 'Full Name',
        change_type: 'modified',
        old_value: {
          properties: {
            maxLength: 50
          }
        },
        new_value: {
          properties: {
            maxLength: 100
          }
        }
      },
      {
        field_id: 'email',
        field_name: 'Email Address',
        change_type: 'added',
        new_value: {
          field_type: 'Email',
          properties: {
            required: true
          }
        }
      },
      {
        field_id: 'phone',
        field_name: 'Phone Number',
        change_type: 'removed',
        old_value: {
          field_type: 'Phone',
          properties: {
            required: false
          }
        }
      }
    ]
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockReset();
  });

  it('renders loading state initially', () => {
    (global.fetch as jest.Mock).mockImplementationOnce(() => 
      new Promise(() => {})
    );

    render(
      <SchemaVersionDiff
        formType="test_form"
        fromVersion="1.0.0"
        toVersion="1.1.0"
      />
    );
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  it('renders diff data after successful fetch', async () => {
    (global.fetch as jest.Mock).mockImplementationOnce(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockDiffData),
      })
    );

    render(
      <SchemaVersionDiff
        formType="test_form"
        fromVersion="1.0.0"
        toVersion="1.1.0"
      />
    );

    await waitFor(() => {
      // Check version headers
      expect(screen.getByText(/Version 1.0.0/)).toBeInTheDocument();
      expect(screen.getByText(/Version 1.1.0/)).toBeInTheDocument();

      // Check modified field
      expect(screen.getByText('name')).toBeInTheDocument();
      expect(screen.getByText('maxLength: 50')).toBeInTheDocument();
      expect(screen.getByText('maxLength: 100')).toBeInTheDocument();

      // Check added field
      expect(screen.getByText('email')).toBeInTheDocument();
      expect(screen.getByText('Added')).toBeInTheDocument();

      // Check removed field
      expect(screen.getByText('phone')).toBeInTheDocument();
      expect(screen.getByText('Removed')).toBeInTheDocument();
    });
  });

  it('shows error message on fetch failure', async () => {
    (global.fetch as jest.Mock).mockImplementationOnce(() =>
      Promise.reject(new Error('Failed to fetch'))
    );

    render(
      <SchemaVersionDiff
        formType="test_form"
        fromVersion="1.0.0"
        toVersion="1.1.0"
      />
    );

    await waitFor(() => {
      expect(message.error).toHaveBeenCalledWith('Failed to load version diff');
    });
  });

  it('displays change types with correct styling', async () => {
    (global.fetch as jest.Mock).mockImplementationOnce(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockDiffData),
      })
    );

    render(
      <SchemaVersionDiff
        formType="test_form"
        fromVersion="1.0.0"
        toVersion="1.1.0"
      />
    );

    await waitFor(() => {
      const addedTag = screen.getByText('Added');
      const removedTag = screen.getByText('Removed');
      const modifiedTag = screen.getByText('Modified');

      expect(addedTag).toHaveStyle({ backgroundColor: expect.stringContaining('green') });
      expect(removedTag).toHaveStyle({ backgroundColor: expect.stringContaining('red') });
      expect(modifiedTag).toHaveStyle({ backgroundColor: expect.stringContaining('blue') });
    });
  });

  it('groups changes by type correctly', async () => {
    (global.fetch as jest.Mock).mockImplementationOnce(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockDiffData),
      })
    );

    render(
      <SchemaVersionDiff
        formType="test_form"
        fromVersion="1.0.0"
        toVersion="1.1.0"
      />
    );

    await waitFor(() => {
      const modifiedSection = screen.getByText('Modified Fields');
      const addedSection = screen.getByText('Added Fields');
      const removedSection = screen.getByText('Removed Fields');

      expect(modifiedSection).toBeInTheDocument();
      expect(addedSection).toBeInTheDocument();
      expect(removedSection).toBeInTheDocument();
    });
  });

  it('displays field details correctly', async () => {
    (global.fetch as jest.Mock).mockImplementationOnce(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockDiffData),
      })
    );

    render(
      <SchemaVersionDiff
        formType="test_form"
        fromVersion="1.0.0"
        toVersion="1.1.0"
      />
    );

    await waitFor(() => {
      // Check field names are displayed
      expect(screen.getByText('Full Name')).toBeInTheDocument();
      expect(screen.getByText('Email Address')).toBeInTheDocument();
      expect(screen.getByText('Phone Number')).toBeInTheDocument();

      // Check field properties are displayed
      expect(screen.getByText(/required: true/)).toBeInTheDocument();
      expect(screen.getByText(/required: false/)).toBeInTheDocument();
      expect(screen.getByText(/field_type: Email/)).toBeInTheDocument();
      expect(screen.getByText(/field_type: Phone/)).toBeInTheDocument();
    });
  });
}); 