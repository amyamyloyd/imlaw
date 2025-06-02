export type ChangeType = 'added' | 'removed' | 'modified';

export interface Position {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface FieldFlags {
  required: boolean;
  readonly?: boolean;
  hidden?: boolean;
}

export interface FormFieldDefinition {
  field_id: string;
  field_type: string;
  field_name: string;
  flags: FieldFlags;
  position: Position;
  properties: Record<string, any>;
  page_number: number;
  tooltip?: string;
}

export interface SchemaVersion {
  version: string;
  form_type: string;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
  created_by?: string;
  approved_at?: string;
  approved_by?: string;
  rejected_at?: string;
  rejected_by?: string;
  rejection_reason?: string;
  comments: Array<{
    text: string;
    created_at: string;
    created_by: string;
  }>;
}

export interface FieldChange {
  field_id: string;
  change_type: ChangeType;
  previous_value: Record<string, any> | null;
  new_value: Record<string, any> | null;
}

export interface VersionDiff {
  from_version: string;
  to_version: string;
  timestamp: string;
  changes: FieldChange[];
}

export interface FormSchema {
  form_type: string;
  version: string;
  title: string;
  fields: FormFieldDefinition[];
  total_fields: number;
} 