import {
  VectorStoreIndex,
  PostgresDocumentStore,
  PostgresIndexStore,
  storageContextFromDefaults,
} from "llamaindex";

import * as dotenv from "dotenv";

import { getDocuments } from "./loader";
import { initSettings } from "./settings";

// Load environment variables from local .env file
dotenv.config();

async function getRuntime(func: any) {
  const start = Date.now();
  await func();
  const end = Date.now();
  return end - start;
}

async function generateDatasource() {
  console.log(`Generating storage context...`);
  // Split documents, create embeddings and store them in the storage context
  const ms = await getRuntime(async () => {

    const storageContext = await storageContextFromDefaults({
      docStore: new PostgresDocumentStore(
        {
          tableName: "idapt_docs",          
        }
      ),
      indexStore: new PostgresIndexStore(
        {
          tableName: "idapt_indexes",
        }
      ),
    });

    const documents = await getDocuments();

    await VectorStoreIndex.fromDocuments(documents, {
      storageContext,
    });
  });
  console.log(`Storage context successfully generated in ${ms / 1000}s.`);
}

(async () => {
  initSettings();
  await generateDatasource();
  console.log("Finished generating storage.");
})();
