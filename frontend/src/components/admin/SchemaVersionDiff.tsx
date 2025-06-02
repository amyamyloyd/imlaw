import React, { useState, useEffect } from 'react';
import { Card, Table, Tag, Collapse, Spin, message } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { FieldChange, ChangeType } from '../../types/schema';

const { Panel } = Collapse;

interface SchemaVersionDiffProps {
  formType: string;
  fromVersion: string;
  toVersion: string;
}

interface DiffData {
  changes: FieldChange[];
  from_version: string;
  to_version: string;
  timestamp: string;
}

const SchemaVersionDiff: React.FC<SchemaVersionDiffProps> = ({
  formType,
  fromVersion,
  toVersion,
}) => {
  const [loading, setLoading] = useState(false);
  const [diffData, setDiffData] = useState<DiffData | null>(null);

  useEffect(() => {
    fetchDiff();
  }, [formType, fromVersion, toVersion]);

  const fetchDiff = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `/api/schema/versions/${fromVersion}/diff/${toVersion}?form_type=${formType}`
      );
      if (!response.ok) throw new Error('Failed to fetch diff');
      const data = await response.json();
      setDiffData(data);
    } catch (error) {
      message.error('Failed to load schema diff');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const getChangeTypeColor = (type: ChangeType) => {
    switch (type) {
      case 'added':
        return 'success';
      case 'removed':
        return 'error';
      case 'modified':
        return 'warning';
      default:
        return 'default';
    }
  };

  const renderFieldValue = (value: any) => {
    if (!value) return <em>None</em>;
    
    return (
      <Collapse>
        <Panel header="Field Details" key="1">
          <pre>{JSON.stringify(value, null, 2)}</pre>
        </Panel>
      </Collapse>
    );
  };

  const columns: ColumnsType<FieldChange> = [
    {
      title: 'Field ID',
      dataIndex: 'field_id',
      key: 'field_id',
      width: '30%',
    },
    {
      title: 'Change Type',
      dataIndex: 'change_type',
      key: 'change_type',
      width: '15%',
      render: (type: ChangeType) => (
        <Tag color={getChangeTypeColor(type)}>
          {type.charAt(0).toUpperCase() + type.slice(1)}
        </Tag>
      ),
      filters: [
        { text: 'Added', value: 'added' },
        { text: 'Removed', value: 'removed' },
        { text: 'Modified', value: 'modified' },
      ],
      onFilter: (value, record) => record.change_type === value,
    },
    {
      title: 'Previous Value',
      dataIndex: 'previous_value',
      key: 'previous_value',
      width: '25%',
      render: renderFieldValue,
    },
    {
      title: 'New Value',
      dataIndex: 'new_value',
      key: 'new_value',
      width: '25%',
      render: renderFieldValue,
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!diffData) {
    return null;
  }

  const { changes } = diffData;
  const stats = {
    added: changes.filter(c => c.change_type === 'added').length,
    removed: changes.filter(c => c.change_type === 'removed').length,
    modified: changes.filter(c => c.change_type === 'modified').length,
  };

  return (
    <div>
      <Card title={`Schema Changes (${fromVersion} → ${toVersion})`}>
        <div style={{ marginBottom: 16 }}>
          <Tag color="success">{stats.added} Added</Tag>
          <Tag color="error">{stats.removed} Removed</Tag>
          <Tag color="warning">{stats.modified} Modified</Tag>
        </div>
        
        <Table
          columns={columns}
          dataSource={changes}
          rowKey="field_id"
          pagination={false}
          expandable={{
            expandedRowRender: record => {
              if (record.change_type === 'modified') {
                const differences = Object.keys(record.new_value || {}).filter(
                  key => JSON.stringify(record.previous_value?.[key]) !== JSON.stringify(record.new_value?.[key])
                );
                
                return (
                  <Card size="small" title="Changed Properties">
                    {differences.map(key => (
                      <div key={key} style={{ marginBottom: 8 }}>
                        <strong>{key}:</strong>
                        <br />
                        Previous: <code>{JSON.stringify(record.previous_value?.[key])}</code>
                        <br />
                        New: <code>{JSON.stringify(record.new_value?.[key])}</code>
                      </div>
                    ))}
                  </Card>
                );
              }
              return null;
            },
            rowExpandable: record => record.change_type === 'modified',
          }}
        />
      </Card>
    </div>
  );
};

export default SchemaVersionDiff; 