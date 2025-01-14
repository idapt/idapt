import { Input } from '../input';
import { Label } from '../label';
import { Textarea } from '../textarea';
import { Switch } from '../switch';

interface ParameterEditorProps {
  schema: Record<string, any>;
  parameters: Record<string, any>;
  onChange: (parameters: Record<string, any>) => void;
}

export function ParameterEditor({ schema, parameters, onChange }: ParameterEditorProps) {
  if (!schema.properties) return null;

  const handleParameterChange = (name: string, value: any) => {
    onChange({
      ...parameters,
      [name]: value
    });
  };

  return (
    <div className="space-y-4">
      {Object.entries(schema.properties).map(([name, prop]: [string, any]) => (
        <div key={name} className="space-y-2">
          <Label className="flex flex-col gap-1">
            <span className="font-medium">{prop.title || name}</span>
            {prop.description && (
              <span className="text-sm text-muted-foreground">
                {prop.description}
              </span>
            )}
          </Label>

          {prop.type === 'integer' && (
            <Input
              type="number"
              value={parameters[name] ?? prop.default ?? ''}
              onChange={(e) => handleParameterChange(name, parseInt(e.target.value, 10))}
              placeholder={`Enter ${name.toLowerCase()}`}
              className="mt-1.5"
            />
          )}

          {prop.type === 'number' && (
            <Input
              type="number"
              value={parameters[name] ?? prop.default ?? ''}
              onChange={(e) => handleParameterChange(name, parseFloat(e.target.value))}
              placeholder={`Enter ${name.toLowerCase()}`}
              step="any"
              className="mt-1.5"
            />
          )}

          {prop.type === 'string' && (
            prop.format === 'textarea' ? (
              <Textarea
                value={parameters[name] ?? prop.default ?? ''}
                onChange={(e) => handleParameterChange(name, e.target.value)}
                placeholder={`Enter ${name.toLowerCase()}`}
                className="mt-1.5"
              />
            ) : (
              <Input
                type="text"
                value={parameters[name] ?? prop.default ?? ''}
                onChange={(e) => handleParameterChange(name, e.target.value)}
                placeholder={`Enter ${name.toLowerCase()}`}
                className="mt-1.5"
              />
            )
          )}

          {prop.type === 'boolean' && (
            <Switch
              checked={parameters[name] ?? prop.default ?? false}
              onCheckedChange={(checked: boolean) => handleParameterChange(name, checked)}
              className="mt-1.5"
            />
          )}
        </div>
      ))}
    </div>
  );
} 