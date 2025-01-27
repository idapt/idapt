import { useEffect, useState } from "react";
import { useApiClient } from "@/app/lib/api-client";
import { DatasourceCreate, DatasourceResponse, DatasourceUpdate } from "@/app/types/datasources";
import { useClientConfig } from "@/app/components/chat/hooks/use-config";

export const useDatasources = () => {
  const { backend } = useClientConfig();
  const { fetchWithAuth } = useApiClient();

  const getAllDatasources = async () => {
    const response = await fetchWithAuth(`${backend}/api/datasources`);
    if (!response.ok) throw new Error('Failed to fetch datasources');
    const datasources: DatasourceResponse[] = await response.json();
    return datasources;
  };

  const getDatasource = async (identifier: string) => {
    const response = await fetchWithAuth(`${backend}/api/datasources/${identifier}`);
    if (!response.ok) throw new Error('Failed to fetch datasource');
    const datasource: DatasourceResponse = await response.json();
    return datasource;
  };

  const deleteDatasource = async (identifier: string) => {
    try {
      const response = await fetchWithAuth(`${backend}/api/datasources/${identifier}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });      
      if (!response.ok) {
          const error = await response.json();
          if (response.status === 409) {
              const detail = error.detail;
              let message = `Some files could not be deleted:\n\n`;
              
              if (detail.processing_files.length > 0) {
                  message += `Files being processed:\n${detail.processing_files.join('\n')}\n\n`;
              }
              
              if (detail.failed_files.length > 0) {
                  message += `Failed to delete:\n${detail.failed_files.join('\n')}\n\n`;
              }
              
              if (detail.deleted_files.length > 0) {
                  message += `Successfully deleted:\n${detail.deleted_files.join('\n')}`;
              }
              
              alert(message);
              return;
          }
          throw new Error(error.detail || 'Failed to delete datasource');
      }
  } catch (error) {
      console.error('Delete failed:', error);
      alert(error instanceof Error ? error.message : 'Failed to delete datasource');
  }
  };

  const createDatasource = async (datasourceCreate: DatasourceCreate) => {
    const response = await fetchWithAuth(`${backend}/api/datasources`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(datasourceCreate)
    });
    if (!response.ok) throw new Error('Failed to create datasource');
  };

  const updateDatasource = async (identifier: string, datasourceUpdate: DatasourceUpdate) => {
    const response = await fetchWithAuth(`${backend}/api/datasources/${identifier}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(datasourceUpdate)
    });
    if (!response.ok) throw new Error('Failed to update datasource');
  };

  return { getAllDatasources, getDatasource, deleteDatasource, createDatasource, updateDatasource };
}
