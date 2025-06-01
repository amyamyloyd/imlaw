export enum DataType {
  STRING = "string",
  NUMBER = "number",
  DATE = "date",
  BOOLEAN = "boolean",
  ARRAY = "array",
  OBJECT = "object"
}

export interface ValidationRule {
  rule_type: string;
  parameters: Record<string, any>;
  error_message?: string;
}

export interface ValidationHistory {
  timestamp: string;
  changed_by: string;
  previous_rules: ValidationRule[];
  new_rules: ValidationRule[];
  reason?: string;
}

export interface UsageStats {
  total_uses: number;
  last_used?: string;
  form_usage: Record<string, number>;
  error_count: number;
}

export interface FormFieldMapping {
  form_type: string;
  form_version: string;
  field_id: string;
  mapping_type: "direct" | "transform" | "composite";
  transform_logic?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface CanonicalField {
  field_name: string;
  display_name: string;
  description?: string;
  data_type: DataType;
  validation_rules: ValidationRule[];
  form_mappings: FormFieldMapping[];
  category?: string;
  required: boolean;
  parent_field?: string;
  group_name?: string;
  dependencies: string[];
  created_at: string;
  updated_at: string;
  aliases: string[];
  source_priority: string[];
  validation_history: ValidationHistory[];
  usage_stats: UsageStats;
  metadata: Record<string, any>;
} 