import {
  BaseChatEngine,
  BaseToolWithCall,
  ReActAgent,
  QueryEngineTool,
} from "llamaindex";
import fs from "node:fs/promises";
import path from "node:path";
import { getDataSource } from "./index";
import { generateFilters } from "./queryFilter";
import { createTools } from "./tools";

export async function createChatEngine(documentIds?: string[], params?: any) {
  const tools: BaseToolWithCall[] = [];

  // Add a query engine tool if we have a data source
  // Delete this code if you don't have a data source
  const index = await getDataSource(params);
  if (index) {
    tools.push(
      new QueryEngineTool({
        queryEngine: index.asQueryEngine({
          preFilters: generateFilters(documentIds || []),
          similarityTopK: process.env.TOP_K ? parseInt(process.env.TOP_K) : 6,
        }),
        metadata: {
          name: "personal_notes_query_engine",
          description: `A query engine for the user's personal notes.`,
        },
      }),
    );
  }

  /*const configFile = path.join("config", "tools.json");
  let toolConfig: any;
  try {
    // add tools from config file if it exists
    toolConfig = JSON.parse(await fs.readFile(configFile, "utf8"));
  } catch (e) {
    console.info(`Could not read ${configFile} file. Using no tools.`);
  }
  if (toolConfig) {
    tools.push(...(await createTools(toolConfig)));
  }*/

  const agent = new ReActAgent({
    tools,
    systemPrompt: process.env.SYSTEM_PROMPT,
  }) as unknown as BaseChatEngine;

  return agent;
}
