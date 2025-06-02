import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { message } from 'antd';
import SchemaVersionList from '../SchemaVersionList';

// Mock fetch
global.fetch = jest.fn();

// Mock antd message
jest.mock('antd', () => ({
  ...jest.requireActual('antd'),
  message: {
    error: jest.fn(),
    success: jest.fn(),
  },
}));

describe('SchemaVersionList', () => {
  const mockVersions = [
    {
      version: '1.0.0',
      form_type: 'test_form',
      status: 'pending',
      created_at: '2024-01-01T00:00:00Z',
      created_by: 'test_user',
      comments: []
    },
    {
      version: '1.1.0',
      form_type: 'test_form',
      status: 'approved',
      created_at: '2024-01-02T00:00:00Z',
      created_by: 'test_user',
      approved_at: '2024-01-03T00:00:00Z',
      approved_by: 'admin_user',
      comments: [
        {
          text: 'Test comment',
          created_at: '2024-01-02T12:00:00Z',
          created_by: 'test_user'
        }
      ]
    }
  ];

  beforeEach(() => {
    // Reset all mocks before each test
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockReset();
  });

  it('renders loading state initially', () => {
    (global.fetch as jest.Mock).mockImplementationOnce(() => 
      new Promise(() => {})
    );

    render(<SchemaVersionList formType="test_form" />);
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  it('renders version list after successful fetch', async () => {
    (global.fetch as jest.Mock).mockImplementationOnce(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockVersions),
      })
    );

    render(<SchemaVersionList formType="test_form" />);

    await waitFor(() => {
      expect(screen.getByText('1.0.0')).toBeInTheDocument();
      expect(screen.getByText('1.1.0')).toBeInTheDocument();
    });
  });

  it('shows error message on fetch failure', async () => {
    (global.fetch as jest.Mock).mockImplementationOnce(() =>
      Promise.reject(new Error('Failed to fetch'))
    );

    render(<SchemaVersionList formType="test_form" />);

    await waitFor(() => {
      expect(message.error).toHaveBeenCalledWith('Failed to load schema versions');
    });
  });

  it('handles version approval', async () => {
    (global.fetch as jest.Mock)
      .mockImplementationOnce(() => // Initial versions fetch
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockVersions),
        })
      )
      .mockImplementationOnce(() => // Approve request
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ message: 'Version approved successfully' }),
        })
      )
      .mockImplementationOnce(() => // Refresh versions fetch
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockVersions),
        })
      );

    render(<SchemaVersionList formType="test_form" />);

    await waitFor(() => {
      expect(screen.getByText('1.0.0')).toBeInTheDocument();
    });

    const approveButton = screen.getAllByText('Approve')[0];
    fireEvent.click(approveButton);

    await waitFor(() => {
      expect(message.success).toHaveBeenCalledWith('Version approved successfully');
    });
  });

  it('handles version rejection', async () => {
    (global.fetch as jest.Mock)
      .mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockVersions),
        })
      )
      .mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ message: 'Version rejected successfully' }),
        })
      )
      .mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockVersions),
        })
      );

    render(<SchemaVersionList formType="test_form" />);

    await waitFor(() => {
      expect(screen.getByText('1.0.0')).toBeInTheDocument();
    });

    const rejectButton = screen.getAllByText('Reject')[0];
    fireEvent.click(rejectButton);

    await waitFor(() => {
      expect(message.success).toHaveBeenCalledWith('Version rejected successfully');
    });
  });

  it('handles adding comments', async () => {
    (global.fetch as jest.Mock)
      .mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockVersions),
        })
      )
      .mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ message: 'Comment added successfully' }),
        })
      )
      .mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockVersions),
        })
      );

    render(<SchemaVersionList formType="test_form" />);

    await waitFor(() => {
      expect(screen.getByText('1.0.0')).toBeInTheDocument();
    });

    const commentButton = screen.getAllByText('Add Comment')[0];
    fireEvent.click(commentButton);

    const commentInput = screen.getByPlaceholderText('Enter your comment');
    fireEvent.change(commentInput, { target: { value: 'Test comment' } });

    const submitButton = screen.getByText('Submit');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(message.success).toHaveBeenCalledWith('Comment added successfully');
    });
  });

  it('displays version details correctly', async () => {
    (global.fetch as jest.Mock).mockImplementationOnce(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockVersions),
      })
    );

    render(<SchemaVersionList formType="test_form" />);

    await waitFor(() => {
      expect(screen.getByText('1.0.0')).toBeInTheDocument();
      expect(screen.getByText('test_user')).toBeInTheDocument();
      expect(screen.getByText('pending')).toBeInTheDocument();
    });
  });
}); 