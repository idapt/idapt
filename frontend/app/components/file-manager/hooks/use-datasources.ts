import { useApiClient } from '@/app/lib/api-client';
import { DatasourceCreate, DatasourceUpdate } from '@/app/client';
import { useUser } from '@/app/contexts/user-context';
import { 
  getAllDatasourcesRouteApiDatasourcesGet,
  getDatasourceRouteApiDatasourcesDatasourceNameGet,
  deleteDatasourceRouteApiDatasourcesDatasourceNameDelete,
  createDatasourceRouteApiDatasourcesDatasourceNamePost,
  updateDatasourceRouteApiDatasourcesDatasourceNamePatch
} from '@/app/client';

export const useDatasources = () => {
  const client = useApiClient();
  const { userId } = useUser();

  const getAllDatasources = async () => {
    const response = await getAllDatasourcesRouteApiDatasourcesGet({
      client,
      query: { user_id: userId }
    });
    return response;
  };

  const getDatasource = async (datasource_name: string) => {
    const response = await getDatasourceRouteApiDatasourcesDatasourceNameGet({
      client,
      path: { datasource_name },
      query: { user_id: userId }
    });
    return response;
  };

  const deleteDatasource = async (datasource_name: string) => {
    try {
      await deleteDatasourceRouteApiDatasourcesDatasourceNameDelete({
        client,
        path: { datasource_name },
        query: { user_id: userId }
      });
    } catch (error) {
      console.error('Delete failed:', error);
      throw error;
    }
  };

  const createDatasource = async (datasource_name: string, datasourceCreate: DatasourceCreate) => {
    await createDatasourceRouteApiDatasourcesDatasourceNamePost({
      client,
      path: { datasource_name },
      query: { user_id: userId },
      body: datasourceCreate
    });
  };

  const updateDatasource = async (datasource_name: string, datasourceUpdate: DatasourceUpdate) => {
    await updateDatasourceRouteApiDatasourcesDatasourceNamePatch({
      client,
      path: { datasource_name },
      query: { user_id: userId },
      body: datasourceUpdate
    });
  };

  return { getAllDatasources, getDatasource, deleteDatasource, createDatasource, updateDatasource };
};