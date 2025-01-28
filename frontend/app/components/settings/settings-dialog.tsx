"use client";

import { useEffect, useState } from "react";
import { X, Plus } from "lucide-react";
import { Button } from "@/app/components/ui/button";
import { Input } from "@/app/components/ui/input";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/app/components/ui/select";
import { useSettingsContext } from "@/app/components/settings/settings-provider";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/app/components/ui/dialog";
import { SettingsEditor } from "./settings-editor";
import { SCHEMA_IDENTIFIER_OPTIONS } from "@/app/types/settings"; // TODO Use a literal in api
import type { SettingResponse } from "@/app/client";

interface SettingsDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SettingsDialog({ isOpen, onClose }: SettingsDialogProps) {
  const [settings, setSettings] = useState<SettingResponse[]>([]);
  const [selectedSetting, setSelectedSetting] = useState<SettingResponse | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [newSettingIdentifier, setNewSettingIdentifier] = useState("");
  const [selectedSchemaId, setSelectedSchemaId] = useState<string>("");
  const { getAllSettings, createSetting, updateSetting, deleteSetting } = useSettingsContext();

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    const settings = await getAllSettings();
    setSettings(settings);
  };

  const handleCreateSetting = async () => {
    try {
      await createSetting(newSettingIdentifier, selectedSchemaId);
      setIsCreating(false);
      setNewSettingIdentifier("");
      setSelectedSchemaId("");
      await loadSettings();
    } catch (error) {
      console.error("Failed to create setting:", error);
      alert("Failed to create setting");
    }
  };

  const handleUpdateSetting = async (identifier: string, valuesToUpdate: Record<string, any> ) => {
    try {
      await updateSetting(
        identifier, 
        valuesToUpdate // Send the value_json directly
      );
      setSelectedSetting(null);
      await loadSettings();
    } catch (error) {
      console.error("Failed to update setting:", error);
      alert("Failed to update setting: " + (error instanceof Error ? error.message : String(error)));
    }
  };

  const handleDeleteSetting = async () => {
    if (!selectedSetting) return;
    
    try {
      if (selectedSetting.identifier === "app") {
        alert("Can't delete app setting");
        return;
      }
      await deleteSetting(selectedSetting.identifier);
      setSelectedSetting(null);
      await loadSettings();
    } catch (error) {
      console.error("Failed to delete setting:", error);
      alert("Failed to delete setting");
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <div className="flex justify-between items-center">
            <DialogTitle>Settings</DialogTitle>
          </div>
        </DialogHeader>

        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <Select value={selectedSetting?.identifier || ''} onValueChange={(id) => {
              const setting = settings.find(s => s.identifier === id);
              setSelectedSetting(setting || null);
            }}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Select setting" />
              </SelectTrigger>
              <SelectContent>
                {settings.map((setting) => (
                  <SelectItem key={setting.identifier} value={setting.identifier}>
                    {setting.identifier} ({setting.schema_identifier})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Button variant="outline" onClick={() => setIsCreating(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create Setting
            </Button>
          </div>

          {isCreating && (
            <div className="space-y-4 p-4 border rounded-lg">
              <h4 className="font-medium">Create New Setting</h4>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Setting ID (hex)</label>
                  <Input
                    value={newSettingIdentifier}
                    onChange={(e) => setNewSettingIdentifier(e.target.value.toLowerCase())}
                    placeholder="e.g. abc123"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Schema Type</label>
                  <Select value={selectedSchemaId} onValueChange={setSelectedSchemaId}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select schema type" />
                    </SelectTrigger>
                    <SelectContent>
                      {SCHEMA_IDENTIFIER_OPTIONS.map((schemaId) => (
                        <SelectItem key={schemaId} value={schemaId}>
                          {schemaId}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex justify-end space-x-2">
                  <Button variant="outline" onClick={() => setIsCreating(false)}>Cancel</Button>
                  <Button onClick={handleCreateSetting} disabled={!newSettingIdentifier || !selectedSchemaId}>
                    Create
                  </Button>
                </div>
              </div>
            </div>
          )}

          {selectedSetting && !isCreating && (
            <SettingsEditor
              setting={selectedSetting}
              onSave={handleUpdateSetting}
              onDelete={handleDeleteSetting}
              onCancel={() => setSelectedSetting(null)}
            />
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
} 