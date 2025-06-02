import React, { useState, useEffect } from 'react';
import { Table, Button, Space, Input, Modal, message } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { SchemaVersion } from '../../types/schema';
import { formatDate } from '../../utils/dateUtils';

interface SchemaVersionListProps {
  formType: string;
}

const SchemaVersionList: React.FC<SchemaVersionListProps> = ({ formType }) => {
  const [versions, setVersions] = useState<SchemaVersion[]>([]);
  const [loading, setLoading] = useState(false);
  const [commentModalVisible, setCommentModalVisible] = useState(false);
  const [selectedVersion, setSelectedVersion] = useState<string | null>(null);
  const [comment, setComment] = useState('');

  useEffect(() => {
    fetchVersions();
  }, [formType]);

  const fetchVersions = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/schema/versions?form_type=${formType}`);
      if (!response.ok) throw new Error('Failed to fetch versions');
      const data = await response.json();
      setVersions(data);
    } catch (error) {
      message.error('Failed to load schema versions');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (version: string) => {
    try {
      const response = await fetch(`/api/schema/versions/${version}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ form_type: formType }),
      });
      if (!response.ok) throw new Error('Failed to approve version');
      message.success('Version approved successfully');
      fetchVersions();
    } catch (error) {
      message.error('Failed to approve version');
      console.error(error);
    }
  };

  const handleReject = async (version: string, reason: string) => {
    try {
      const response = await fetch(`/api/schema/versions/${version}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ form_type: formType, reason }),
      });
      if (!response.ok) throw new Error('Failed to reject version');
      message.success('Version rejected successfully');
      fetchVersions();
    } catch (error) {
      message.error('Failed to reject version');
      console.error(error);
    }
  };

  const handleRevert = async (version: string) => {
    try {
      const response = await fetch(`/api/schema/versions/${version}/revert`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ form_type: formType }),
      });
      if (!response.ok) throw new Error('Failed to revert version');
      message.success('Reverted to version successfully');
      fetchVersions();
    } catch (error) {
      message.error('Failed to revert to version');
      console.error(error);
    }
  };

  const handleAddComment = async () => {
    if (!selectedVersion || !comment.trim()) return;

    try {
      const response = await fetch(`/api/schema/versions/${selectedVersion}/comment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ form_type: formType, comment }),
      });
      if (!response.ok) throw new Error('Failed to add comment');
      message.success('Comment added successfully');
      setCommentModalVisible(false);
      setComment('');
      fetchVersions();
    } catch (error) {
      message.error('Failed to add comment');
      console.error(error);
    }
  };

  const columns: ColumnsType<SchemaVersion> = [
    {
      title: 'Version',
      dataIndex: 'version',
      key: 'version',
      sorter: (a, b) => a.version.localeCompare(b.version),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      filters: [
        { text: 'Pending', value: 'pending' },
        { text: 'Approved', value: 'approved' },
        { text: 'Rejected', value: 'rejected' },
      ],
      onFilter: (value, record) => record.status === value,
    },
    {
      title: 'Created At',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => formatDate(date),
      sorter: (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            onClick={() => window.location.href = `/admin/schema/${formType}/version/${record.version}`}
          >
            View
          </Button>
          {record.status === 'pending' && (
            <>
              <Button type="primary" onClick={() => handleApprove(record.version)}>
                Approve
              </Button>
              <Button danger onClick={() => {
                Modal.confirm({
                  title: 'Reject Version',
                  content: (
                    <Input.TextArea
                      placeholder="Enter rejection reason"
                      onChange={(e) => setComment(e.target.value)}
                    />
                  ),
                  onOk: () => handleReject(record.version, comment),
                });
              }}>
                Reject
              </Button>
            </>
          )}
          <Button
            onClick={() => {
              setSelectedVersion(record.version);
              setCommentModalVisible(true);
            }}
          >
            Add Comment
          </Button>
          {record.status === 'approved' && (
            <Button
              onClick={() => {
                Modal.confirm({
                  title: 'Revert to Version',
                  content: 'Are you sure you want to revert to this version?',
                  onOk: () => handleRevert(record.version),
                });
              }}
            >
              Revert
            </Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <h2>Schema Versions - {formType}</h2>
      <Table
        columns={columns}
        dataSource={versions}
        loading={loading}
        rowKey="version"
        pagination={{ pageSize: 10 }}
      />
      
      <Modal
        title="Add Comment"
        open={commentModalVisible}
        onOk={handleAddComment}
        onCancel={() => {
          setCommentModalVisible(false);
          setComment('');
        }}
      >
        <Input.TextArea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Enter your comment"
          rows={4}
        />
      </Modal>
    </div>
  );
};

export default SchemaVersionList; 