import { useApiClient } from '@/app/lib/api-client';
import { DatasourceCreate, DatasourceUpdate } from '@/app/client';
import { useUser } from '@/app/contexts/user-context';
import { 
  getDatasourcesRouteApiDatasourcesGet,
  getDatasourceRouteApiDatasourcesIdentifierGet,
  deleteDatasourceRouteApiDatasourcesIdentifierDelete,
  createDatasourceRouteApiDatasourcesPost,
  updateDatasourceRouteApiDatasourcesIdentifierPatch
} from '@/app/client';

export const useDatasources = () => {
  const client = useApiClient();
  const { userId } = useUser();

  const getAllDatasources = async () => {
    const response = await getDatasourcesRouteApiDatasourcesGet({
      client,
      query: { user_id: userId }
    });
    return response;
  };

  const getDatasource = async (identifier: string) => {
    const response = await getDatasourceRouteApiDatasourcesIdentifierGet({
      client,
      path: { identifier },
      query: { user_id: userId }
    });
    return response;
  };

  const deleteDatasource = async (identifier: string) => {
    try {
      await deleteDatasourceRouteApiDatasourcesIdentifierDelete({
        client,
        path: { identifier },
        query: { user_id: userId }
      });
    } catch (error) {
      console.error('Delete failed:', error);
      throw error;
    }
  };

  const createDatasource = async (datasourceCreate: DatasourceCreate) => {
    await createDatasourceRouteApiDatasourcesPost({
      client,
      query: { user_id: userId },
      body: datasourceCreate
    });
  };

  const updateDatasource = async (identifier: string, datasourceUpdate: DatasourceUpdate) => {
    await updateDatasourceRouteApiDatasourcesIdentifierPatch({
      client,
      path: { identifier },
      query: { user_id: userId },
      body: datasourceUpdate
    });
  };

  return { getAllDatasources, getDatasource, deleteDatasource, createDatasource, updateDatasource };
};