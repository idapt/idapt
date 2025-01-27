import { useState } from "react";
import { Button } from "@/app/components/ui/button";
import { Input } from "@/app/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/app/components/ui/select";
import { Trash2 } from "lucide-react";
import type { Setting, JsonSchema, FieldSchema } from "@/app/types/settings";

interface SettingsEditorProps {
  setting: Setting;
  onSave: (identifier: string, valuesToUpdate: Record<string, any>) => Promise<void>;
  onDelete: () => Promise<void>;
  onCancel: () => void;
}

export function SettingsEditor({ setting, onSave, onDelete, onCancel }: SettingsEditorProps) {
  const [valuesToUpdate, setValuesToChange] = useState<Record<string, any>>({});
  const schema: JsonSchema = JSON.parse(setting.setting_schema_json);

  const updateField = (field: string, newValue: any) => {
    try {
      setValuesToChange({
        ...valuesToUpdate,
        [field]: newValue
      });
    } catch (error) {
      console.error("Error updating field:", error);
    }
  };

  const getFieldValue = (fieldName: string, fieldSchema: FieldSchema) => {
    if (valuesToUpdate[fieldName]) {
      return valuesToUpdate[fieldName] ?? fieldSchema.default ?? '';
    }
    else {
      // Use the initial value from the setting
      const values = JSON.parse(setting.value_json);
      return values[fieldName] ?? fieldSchema.default ?? '';
    }
  };

  const renderField = (fieldName: string, fieldSchema: FieldSchema) => {
    const fieldValue = getFieldValue(fieldName, fieldSchema);
    const isRequired = schema.required?.includes(fieldName) || false;

    switch (fieldSchema.type) {
      case "string":
        if (fieldSchema.enum) {
          return (
            <div key={fieldName} className="space-y-2">
              <label className="text-sm font-medium">
                {fieldSchema.title || fieldName}
                {isRequired && " *"}
              </label>
              <Select 
                value={fieldValue.toString()} 
                onValueChange={(v) => updateField(fieldName, v)}
              >
                <SelectTrigger>
                  <SelectValue placeholder={`Select ${fieldName}`} />
                </SelectTrigger>
                <SelectContent>
                  {fieldSchema.enum.map((option) => (
                    <SelectItem key={option} value={option}>
                      {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {fieldSchema.description && (
                <p className="text-xs text-muted-foreground mt-1">{fieldSchema.description}</p>
              )}
            </div>
          );
        }
        return (
          <div key={fieldName} className="space-y-2">
            <label className="text-sm font-medium">
              {fieldSchema.title || fieldName}
              {isRequired && " *"}
            </label>
            <Input
              type={fieldSchema.format === "password" ? "password" : "text"}
              value={fieldValue}
              onChange={(e) => updateField(fieldName, e.target.value)}
              placeholder={fieldSchema.description}
            />
            {fieldSchema.description && (
              <p className="text-xs text-muted-foreground mt-1">{fieldSchema.description}</p>
            )}
          </div>
        );

      case "integer":
      case "number":
        return (
          <div key={fieldName} className="space-y-2">
            <label className="text-sm font-medium">
              {fieldSchema.title || fieldName}
              {isRequired && " *"}
            </label>
            <Input
              type="number"
              value={fieldValue}
              onChange={(e) => updateField(fieldName, parseFloat(e.target.value))}
              min={fieldSchema.minimum}
              max={fieldSchema.maximum}
              step={fieldSchema.type === "integer" ? 1 : "any"}
            />
            {fieldSchema.description && (
              <p className="text-xs text-muted-foreground mt-1">{fieldSchema.description}</p>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="space-y-4">
      <div className="space-y-4">
        {Object.entries(schema.properties)
          .filter(([key]) => !["identifier", "schema_identifier"].includes(key))
          .map(([fieldName, fieldSchema]) => renderField(fieldName, fieldSchema))}
      </div>

      <div className="flex justify-between pt-4 border-t">
        <Button variant="destructive" onClick={onDelete}>
          <Trash2 className="h-4 w-4 mr-2" />
          Delete Setting
        </Button>
        <div className="space-x-2">
          <Button variant="outline" onClick={onCancel}>Cancel</Button>
          <Button onClick={() => {onSave(setting.identifier, valuesToUpdate);}}>Save Changes</Button>
        </div>
      </div>
    </div>
  );
} 