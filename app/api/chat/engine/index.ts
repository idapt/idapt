import {
  VectorStoreIndex,
  storageContextFromDefaults,
} from "llamaindex";
// Need to import from the node_modules folder otherwise we get a webpack error
import { PostgresDocumentStore } from "llamaindex/storage/docStore/PostgresDocumentStore";
import { PostgresIndexStore } from "llamaindex/storage/indexStore/PostgresIndexStore";

export async function getDataSource(params?: any) {
  try {
    const storageContext = await storageContextFromDefaults({
      docStore: new PostgresDocumentStore({
        tableName: "idapt_docs",
      }),
      indexStore: new PostgresIndexStore({
        tableName: "idapt_indexes",
      }),
    });

    const numberOfDocs = await (storageContext.docStore as PostgresDocumentStore)
      .docs()
      .then((docs) => Object.keys(docs).length);

    if (numberOfDocs === 0) {
      return null;
    }

    return await VectorStoreIndex.init({
      storageContext,
    });
  } catch (error) {
    console.error("Error initializing data source:", error);
    throw error;
  }
}
