// This file is auto-generated by @hey-api/openapi-ts

/**
 * An annotation from the agent that is a text and an agent name.
 */
export type AgentAnnotation = {
    agent: string;
    text: string;
};

export type AllSettingsResponse = {
    data: Array<SettingResponse>;
};

/**
 * An annotation on a message used to pass additional data about the message.
 * The type of the annotation is a string that can be one of the following:
 * - "document_file": A file uploaded by the user.
 * - "image": An image uploaded by the user.
 * - "agent": An annotation from the agent.
 * - "artifact": An artifact from the agent.
 * The data is one of the following types:
 * - AnnotationFileData: A file uploaded by the user.
 * - List[str]: A list of strings.
 * - AgentAnnotation: An annotation from the agent.
 * - ArtifactAnnotation: An artifact from the agent.
 */
export type AnnotationInput = {
    type: string;
    data: AnnotationFileDataInput | Array<string> | AgentAnnotation | ArtifactAnnotation;
};

/**
 * An annotation on a message used to pass additional data about the message.
 * The type of the annotation is a string that can be one of the following:
 * - "document_file": A file uploaded by the user.
 * - "image": An image uploaded by the user.
 * - "agent": An annotation from the agent.
 * - "artifact": An artifact from the agent.
 * The data is one of the following types:
 * - AnnotationFileData: A file uploaded by the user.
 * - List[str]: A list of strings.
 * - AgentAnnotation: An annotation from the agent.
 * - ArtifactAnnotation: An artifact from the agent.
 */
export type AnnotationOutput = {
    type: string;
    data: AnnotationFileDataOutput | Array<string> | AgentAnnotation | ArtifactAnnotation;
};

/**
 * A list of files used as context to generate the response.
 */
export type AnnotationFileDataInput = {
    /**
     * List of files
     */
    files?: Array<DocumentFileInput>;
};

/**
 * A list of files used as context to generate the response.
 */
export type AnnotationFileDataOutput = {
    /**
     * List of files
     */
    files?: Array<DocumentFileOutput>;
};

/**
 * An artifact from the agent that is a tool call and tool output.
 */
export type ArtifactAnnotation = {
    toolCall: {
        [key: string]: unknown;
    };
    toolOutput: {
        [key: string]: unknown;
    };
};

/**
 * Chat received from the vercel ai sdk from the frontend
 * Follows openai chat format + vercel ai sdk format
 */
export type ChatDataInput = {
    id: string;
    messages: Array<MessageDataInput> | null;
    chat_engine_params?: unknown;
};

/**
 * Chat received from the vercel ai sdk from the frontend
 * Follows openai chat format + vercel ai sdk format
 */
export type ChatDataOutput = {
    id: string;
    messages: Array<MessageDataOutput> | null;
    chat_engine_params?: unknown;
};

/**
 * Used in the backend to get a chat
 */
export type ChatResponse = {
    uuid: string;
    title: string;
    created_at: string;
    last_message_at: string;
    last_opened_at: string;
    messages: Array<MessageResponse>;
};

export type CreateSettingRequest = {
    schema_identifier: string;
};

export type DatasourceCreate = {
    name: string;
    type: 'files' | 'windows_sync';
    description?: string | null;
    settings_json?: string;
    embedding_setting_identifier?: string;
};

export type DatasourceResponse = {
    identifier: string;
    name: string;
    type: DatasourceType;
    description?: string | null;
    settings_json?: string;
    embedding_setting_identifier: string;
};

export type DatasourceType = 'files' | 'windows_sync';

export type DatasourceUpdate = {
    description?: string | null;
    embedding_setting_identifier?: string | null;
};

export type DocumentFileInput = {
    id: string;
    name: string;
    type?: string;
    size?: number;
    url?: string;
    /**
     * The stored file path. Used internally in the server.
     */
    path?: string | null;
    /**
     * The document ids in the index.
     */
    refs?: Array<string> | null;
};

export type DocumentFileOutput = {
    id: string;
    name: string;
    type?: string;
    size?: number;
    url?: string;
    /**
     * The document ids in the index.
     */
    refs?: Array<string> | null;
};

export type FileInfoResponse = {
    id: number;
    name: string;
    path: string;
    original_path: string;
    content?: string | null;
    mime_type?: string | null;
    size?: number | null;
    uploaded_at: number;
    accessed_at: number;
    file_created_at: number;
    file_modified_at: number;
    stacks_to_process?: string | null;
    processed_stacks?: string | null;
    error_message?: string | null;
    status: string;
};

export type FileUploadItem = {
    original_path: string;
    base64_content: string;
    name: string;
    file_created_at: number;
    file_modified_at: number;
};

export type FolderInfoResponse = {
    id: number;
    name: string;
    path: string;
    original_path: string;
    uploaded_at: number;
    accessed_at: number;
    child_folders?: Array<FolderInfoResponse> | null;
    child_files?: Array<FileInfoResponse> | null;
};

export type HttpValidationError = {
    detail?: Array<ValidationError>;
};

export type ItemProcessingStatusResponse = {
    original_path: string;
    name: string;
    queued_stacks: Array<string>;
    status: 'pending' | 'processing' | 'queued' | 'completed' | 'error';
};

/**
 * Used in the backend to create a message / add a message to a chat
 */
export type MessageCreate = {
    uuid: string;
    role: MessageRole;
    content: string;
    annotations: Array<AnnotationInput> | null;
    created_at: string;
};

/**
 * Messages received from the vercel ai sdk from the frontend
 * Follows openai message format + vercel ai sdk format
 */
export type MessageDataInput = {
    id: string;
    role: MessageRole;
    content: string;
    createdAt: string;
    annotations?: Array<AnnotationInput> | null;
    is_upvoted?: boolean | null;
};

/**
 * Messages received from the vercel ai sdk from the frontend
 * Follows openai message format + vercel ai sdk format
 */
export type MessageDataOutput = {
    id: string;
    role: MessageRole;
    content: string;
    createdAt: string;
    annotations?: Array<AnnotationOutput> | null;
    is_upvoted?: boolean | null;
};

/**
 * Used in the backend to get a message
 */
export type MessageResponse = {
    uuid: string;
    role: 'system' | 'user' | 'assistant' | 'function' | 'tool' | 'chatbot' | 'model';
    content: string;
    annotations: Array<AnnotationOutput> | null;
    is_upvoted: boolean | null;
    created_at: string;
};

/**
 * Message role.
 */
export type MessageRole = 'system' | 'user' | 'assistant' | 'function' | 'tool' | 'chatbot' | 'model';

export type OllamaStatusResponse = {
    is_downloading: boolean;
};

export type ProcessingItem = {
    original_path: string;
    stacks_identifiers_to_queue: Array<string>;
};

export type ProcessingRequest = {
    items: Array<ProcessingItem>;
};

export type ProcessingStackCreate = {
    display_name: string;
    description?: string | null;
    supported_extensions?: Array<string> | null;
    steps?: Array<ProcessingStackStepCreate> | null;
};

export type ProcessingStackResponse = {
    identifier: string;
    display_name: string;
    description?: string | null;
    supported_extensions: Array<string>;
    is_enabled: boolean;
    steps: Array<ProcessingStackStepResponse>;
};

export type ProcessingStackStepCreate = {
    step_identifier: string;
    order: number;
    parameters: {
        [key: string]: unknown;
    };
};

export type ProcessingStackStepResponse = {
    id: number;
    order: number;
    parameters?: {
        [key: string]: unknown;
    } | null;
    step_identifier: string;
    step: ProcessingStepResponse;
};

export type ProcessingStackStepUpdate = {
    step_identifier: string;
    order: number;
    parameters?: {
        [key: string]: unknown;
    } | null;
};

export type ProcessingStackUpdate = {
    steps: Array<ProcessingStackStepUpdate>;
    supported_extensions: Array<string>;
};

export type ProcessingStatusResponse = {
    queued_count: number;
    queued_items: Array<ItemProcessingStatusResponse>;
    processing_count: number;
    processing_items: Array<ItemProcessingStatusResponse>;
};

export type ProcessingStepResponse = {
    identifier: string;
    display_name: string;
    description?: string | null;
    type: string;
    parameters_schema: {
        [key: string]: unknown;
    };
};

export type SettingResponse = {
    identifier: string;
    schema_identifier: string;
    setting_schema_json: string;
    value_json: string;
};

export type UpdateSettingRequest = {
    values_to_update_json: string;
};

export type ValidationError = {
    loc: Array<string | number>;
    msg: string;
    type: string;
};

export type ChatStreamingRouteApiChatPostData = {
    body: ChatDataInput;
    headers?: {
        'x-user-id'?: string | null;
    };
    path?: never;
    query: {
        user_id: string;
    };
    url: '/api/chat';
};

export type ChatStreamingRouteApiChatPostErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type ChatStreamingRouteApiChatPostError = ChatStreamingRouteApiChatPostErrors[keyof ChatStreamingRouteApiChatPostErrors];

export type ChatStreamingRouteApiChatPostResponses = {
    /**
     * Successful Response
     */
    200: unknown;
};

export type ChatRequestRouteApiChatRequestPostData = {
    body: ChatDataInput;
    headers?: {
        'x-user-id'?: string | null;
    };
    path?: never;
    query: {
        user_id: string;
    };
    url: '/api/chat/request';
};

export type ChatRequestRouteApiChatRequestPostErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type ChatRequestRouteApiChatRequestPostError = ChatRequestRouteApiChatRequestPostErrors[keyof ChatRequestRouteApiChatRequestPostErrors];

export type ChatRequestRouteApiChatRequestPostResponses = {
    /**
     * Successful Response
     */
    200: ChatDataOutput;
};

export type ChatRequestRouteApiChatRequestPostResponse = ChatRequestRouteApiChatRequestPostResponses[keyof ChatRequestRouteApiChatRequestPostResponses];

export type DeleteSettingRouteApiSettingsIdentifierDeleteData = {
    body?: never;
    headers?: {
        'x-user-id'?: string | null;
    };
    path: {
        identifier: string;
    };
    query: {
        user_id: string;
    };
    url: '/api/settings/{identifier}';
};

export type DeleteSettingRouteApiSettingsIdentifierDeleteErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type DeleteSettingRouteApiSettingsIdentifierDeleteError = DeleteSettingRouteApiSettingsIdentifierDeleteErrors[keyof DeleteSettingRouteApiSettingsIdentifierDeleteErrors];

export type DeleteSettingRouteApiSettingsIdentifierDeleteResponses = {
    /**
     * Successful Response
     */
    200: unknown;
};

export type GetSettingRouteApiSettingsIdentifierGetData = {
    body?: never;
    headers?: {
        'x-user-id'?: string | null;
    };
    path: {
        identifier: string;
    };
    query: {
        user_id: string;
    };
    url: '/api/settings/{identifier}';
};

export type GetSettingRouteApiSettingsIdentifierGetErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type GetSettingRouteApiSettingsIdentifierGetError = GetSettingRouteApiSettingsIdentifierGetErrors[keyof GetSettingRouteApiSettingsIdentifierGetErrors];

export type GetSettingRouteApiSettingsIdentifierGetResponses = {
    /**
     * Successful Response
     */
    200: SettingResponse;
};

export type GetSettingRouteApiSettingsIdentifierGetResponse = GetSettingRouteApiSettingsIdentifierGetResponses[keyof GetSettingRouteApiSettingsIdentifierGetResponses];

export type UpdateSettingRouteApiSettingsIdentifierPatchData = {
    body: UpdateSettingRequest;
    headers?: {
        'x-user-id'?: string | null;
    };
    path: {
        identifier: string;
    };
    query: {
        user_id: string;
    };
    url: '/api/settings/{identifier}';
};

export type UpdateSettingRouteApiSettingsIdentifierPatchErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type UpdateSettingRouteApiSettingsIdentifierPatchError = UpdateSettingRouteApiSettingsIdentifierPatchErrors[keyof UpdateSettingRouteApiSettingsIdentifierPatchErrors];

export type UpdateSettingRouteApiSettingsIdentifierPatchResponses = {
    /**
     * Successful Response
     */
    200: unknown;
};

export type CreateSettingRouteApiSettingsIdentifierPostData = {
    body: CreateSettingRequest;
    headers?: {
        'x-user-id'?: string | null;
    };
    path: {
        identifier: string;
    };
    query: {
        user_id: string;
    };
    url: '/api/settings/{identifier}';
};

export type CreateSettingRouteApiSettingsIdentifierPostErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type CreateSettingRouteApiSettingsIdentifierPostError = CreateSettingRouteApiSettingsIdentifierPostErrors[keyof CreateSettingRouteApiSettingsIdentifierPostErrors];

export type CreateSettingRouteApiSettingsIdentifierPostResponses = {
    /**
     * Successful Response
     */
    200: unknown;
};

export type GetAllSettingsRouteApiSettingsGetData = {
    body?: never;
    headers?: {
        'x-user-id'?: string | null;
    };
    path?: never;
    query: {
        user_id: string;
    };
    url: '/api/settings';
};

export type GetAllSettingsRouteApiSettingsGetErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type GetAllSettingsRouteApiSettingsGetError = GetAllSettingsRouteApiSettingsGetErrors[keyof GetAllSettingsRouteApiSettingsGetErrors];

export type GetAllSettingsRouteApiSettingsGetResponses = {
    /**
     * Successful Response
     */
    200: AllSettingsResponse;
};

export type GetAllSettingsRouteApiSettingsGetResponse = GetAllSettingsRouteApiSettingsGetResponses[keyof GetAllSettingsRouteApiSettingsGetResponses];

export type UploadFileRouteApiDatasourcesFileManagerUploadFilePostData = {
    body: FileUploadItem;
    headers?: {
        'x-user-id'?: string | null;
    };
    path?: never;
    query: {
        user_id: string;
    };
    url: '/api/datasources/file-manager/upload-file';
};

export type UploadFileRouteApiDatasourcesFileManagerUploadFilePostErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type UploadFileRouteApiDatasourcesFileManagerUploadFilePostError = UploadFileRouteApiDatasourcesFileManagerUploadFilePostErrors[keyof UploadFileRouteApiDatasourcesFileManagerUploadFilePostErrors];

export type UploadFileRouteApiDatasourcesFileManagerUploadFilePostResponses = {
    /**
     * Successful Response
     */
    200: FileInfoResponse;
};

export type UploadFileRouteApiDatasourcesFileManagerUploadFilePostResponse = UploadFileRouteApiDatasourcesFileManagerUploadFilePostResponses[keyof UploadFileRouteApiDatasourcesFileManagerUploadFilePostResponses];

export type DeleteRouteApiDatasourcesFileManagerEncodedOriginalPathDeleteData = {
    body?: never;
    headers?: {
        'x-user-id'?: string | null;
    };
    path: {
        encoded_original_path: string;
    };
    query: {
        user_id: string;
    };
    url: '/api/datasources/file-manager/{encoded_original_path}';
};

export type DeleteRouteApiDatasourcesFileManagerEncodedOriginalPathDeleteErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type DeleteRouteApiDatasourcesFileManagerEncodedOriginalPathDeleteError = DeleteRouteApiDatasourcesFileManagerEncodedOriginalPathDeleteErrors[keyof DeleteRouteApiDatasourcesFileManagerEncodedOriginalPathDeleteErrors];

export type DeleteRouteApiDatasourcesFileManagerEncodedOriginalPathDeleteResponses = {
    /**
     * Successful Response
     */
    200: unknown;
};

export type GetFolderInfoRouteApiDatasourcesFileManagerFolderEncodedOriginalPathGetData = {
    body?: never;
    headers?: {
        'x-user-id'?: string | null;
    };
    path: {
        encoded_original_path: string;
    };
    query: {
        include_child_folders_files_recursively?: boolean;
        user_id: string;
    };
    url: '/api/datasources/file-manager/folder/{encoded_original_path}';
};

export type GetFolderInfoRouteApiDatasourcesFileManagerFolderEncodedOriginalPathGetErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type GetFolderInfoRouteApiDatasourcesFileManagerFolderEncodedOriginalPathGetError = GetFolderInfoRouteApiDatasourcesFileManagerFolderEncodedOriginalPathGetErrors[keyof GetFolderInfoRouteApiDatasourcesFileManagerFolderEncodedOriginalPathGetErrors];

export type GetFolderInfoRouteApiDatasourcesFileManagerFolderEncodedOriginalPathGetResponses = {
    /**
     * Successful Response
     */
    200: FolderInfoResponse;
};

export type GetFolderInfoRouteApiDatasourcesFileManagerFolderEncodedOriginalPathGetResponse = GetFolderInfoRouteApiDatasourcesFileManagerFolderEncodedOriginalPathGetResponses[keyof GetFolderInfoRouteApiDatasourcesFileManagerFolderEncodedOriginalPathGetResponses];

export type GetFileInfoRouteApiDatasourcesFileManagerFileEncodedOriginalPathGetData = {
    body?: never;
    headers?: {
        'x-user-id'?: string | null;
    };
    path: {
        encoded_original_path: string;
    };
    query: {
        include_content?: boolean;
        user_id: string;
    };
    url: '/api/datasources/file-manager/file/{encoded_original_path}';
};

export type GetFileInfoRouteApiDatasourcesFileManagerFileEncodedOriginalPathGetErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type GetFileInfoRouteApiDatasourcesFileManagerFileEncodedOriginalPathGetError = GetFileInfoRouteApiDatasourcesFileManagerFileEncodedOriginalPathGetErrors[keyof GetFileInfoRouteApiDatasourcesFileManagerFileEncodedOriginalPathGetErrors];

export type GetFileInfoRouteApiDatasourcesFileManagerFileEncodedOriginalPathGetResponses = {
    /**
     * Successful Response
     */
    200: FileInfoResponse;
};

export type GetFileInfoRouteApiDatasourcesFileManagerFileEncodedOriginalPathGetResponse = GetFileInfoRouteApiDatasourcesFileManagerFileEncodedOriginalPathGetResponses[keyof GetFileInfoRouteApiDatasourcesFileManagerFileEncodedOriginalPathGetResponses];

export type DownloadFileRouteApiDatasourcesFileManagerFileEncodedOriginalPathDownloadGetData = {
    body?: never;
    headers?: {
        'x-user-id'?: string | null;
    };
    path: {
        encoded_original_path: string;
    };
    query: {
        user_id: string;
    };
    url: '/api/datasources/file-manager/file/{encoded_original_path}/download';
};

export type DownloadFileRouteApiDatasourcesFileManagerFileEncodedOriginalPathDownloadGetErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type DownloadFileRouteApiDatasourcesFileManagerFileEncodedOriginalPathDownloadGetError = DownloadFileRouteApiDatasourcesFileManagerFileEncodedOriginalPathDownloadGetErrors[keyof DownloadFileRouteApiDatasourcesFileManagerFileEncodedOriginalPathDownloadGetErrors];

export type DownloadFileRouteApiDatasourcesFileManagerFileEncodedOriginalPathDownloadGetResponses = {
    /**
     * Successful Response
     */
    200: unknown;
};

export type DownloadFolderRouteApiDatasourcesFileManagerFolderEncodedOriginalPathDownloadGetData = {
    body?: never;
    headers?: {
        'x-user-id'?: string | null;
    };
    path: {
        encoded_original_path: string;
    };
    query: {
        user_id: string;
    };
    url: '/api/datasources/file-manager/folder/{encoded_original_path}/download';
};

export type DownloadFolderRouteApiDatasourcesFileManagerFolderEncodedOriginalPathDownloadGetErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type DownloadFolderRouteApiDatasourcesFileManagerFolderEncodedOriginalPathDownloadGetError = DownloadFolderRouteApiDatasourcesFileManagerFolderEncodedOriginalPathDownloadGetErrors[keyof DownloadFolderRouteApiDatasourcesFileManagerFolderEncodedOriginalPathDownloadGetErrors];

export type DownloadFolderRouteApiDatasourcesFileManagerFolderEncodedOriginalPathDownloadGetResponses = {
    /**
     * Successful Response
     */
    200: unknown;
};

export type DeleteProcessedDataRouteApiDatasourcesFileManagerProcessedDataEncodedOriginalPathDeleteData = {
    body?: never;
    headers?: {
        'x-user-id'?: string | null;
    };
    path: {
        encoded_original_path: string;
    };
    query: {
        user_id: string;
    };
    url: '/api/datasources/file-manager/processed-data/{encoded_original_path}';
};

export type DeleteProcessedDataRouteApiDatasourcesFileManagerProcessedDataEncodedOriginalPathDeleteErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type DeleteProcessedDataRouteApiDatasourcesFileManagerProcessedDataEncodedOriginalPathDeleteError = DeleteProcessedDataRouteApiDatasourcesFileManagerProcessedDataEncodedOriginalPathDeleteErrors[keyof DeleteProcessedDataRouteApiDatasourcesFileManagerProcessedDataEncodedOriginalPathDeleteErrors];

export type DeleteProcessedDataRouteApiDatasourcesFileManagerProcessedDataEncodedOriginalPathDeleteResponses = {
    /**
     * Successful Response
     */
    200: unknown;
};

export type GetAllChatsRouteApiDatasourcesChatsGetData = {
    body?: never;
    headers?: {
        'x-user-id'?: string | null;
    };
    path?: never;
    query: {
        include_messages?: boolean;
        user_id: string;
    };
    url: '/api/datasources/chats';
};

export type GetAllChatsRouteApiDatasourcesChatsGetErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type GetAllChatsRouteApiDatasourcesChatsGetError = GetAllChatsRouteApiDatasourcesChatsGetErrors[keyof GetAllChatsRouteApiDatasourcesChatsGetErrors];

export type GetAllChatsRouteApiDatasourcesChatsGetResponses = {
    /**
     * Successful Response
     */
    200: Array<ChatResponse>;
};

export type GetAllChatsRouteApiDatasourcesChatsGetResponse = GetAllChatsRouteApiDatasourcesChatsGetResponses[keyof GetAllChatsRouteApiDatasourcesChatsGetResponses];

export type CreateChatRouteApiDatasourcesChatsPostData = {
    body?: never;
    headers?: {
        'x-user-id'?: string | null;
    };
    path?: never;
    query: {
        chat_uuid?: string;
        user_id: string;
    };
    url: '/api/datasources/chats';
};

export type CreateChatRouteApiDatasourcesChatsPostErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type CreateChatRouteApiDatasourcesChatsPostError = CreateChatRouteApiDatasourcesChatsPostErrors[keyof CreateChatRouteApiDatasourcesChatsPostErrors];

export type CreateChatRouteApiDatasourcesChatsPostResponses = {
    /**
     * Successful Response
     */
    201: ChatResponse;
};

export type CreateChatRouteApiDatasourcesChatsPostResponse = CreateChatRouteApiDatasourcesChatsPostResponses[keyof CreateChatRouteApiDatasourcesChatsPostResponses];

export type DeleteChatRouteApiDatasourcesChatsChatUuidDeleteData = {
    body?: never;
    headers?: {
        'x-user-id'?: string | null;
    };
    path: {
        chat_uuid: string;
    };
    query: {
        user_id: string;
    };
    url: '/api/datasources/chats/{chat_uuid}';
};

export type DeleteChatRouteApiDatasourcesChatsChatUuidDeleteErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type DeleteChatRouteApiDatasourcesChatsChatUuidDeleteError = DeleteChatRouteApiDatasourcesChatsChatUuidDeleteErrors[keyof DeleteChatRouteApiDatasourcesChatsChatUuidDeleteErrors];

export type DeleteChatRouteApiDatasourcesChatsChatUuidDeleteResponses = {
    /**
     * Successful Response
     */
    200: unknown;
};

export type GetChatRouteApiDatasourcesChatsChatUuidGetData = {
    body?: never;
    headers?: {
        'x-user-id'?: string | null;
    };
    path: {
        chat_uuid: string;
    };
    query: {
        include_messages?: boolean;
        create_if_not_found?: boolean;
        update_last_opened_at?: boolean;
        user_id: string;
    };
    url: '/api/datasources/chats/{chat_uuid}';
};

export type GetChatRouteApiDatasourcesChatsChatUuidGetErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type GetChatRouteApiDatasourcesChatsChatUuidGetError = GetChatRouteApiDatasourcesChatsChatUuidGetErrors[keyof GetChatRouteApiDatasourcesChatsChatUuidGetErrors];

export type GetChatRouteApiDatasourcesChatsChatUuidGetResponses = {
    /**
     * Successful Response
     */
    200: ChatResponse;
};

export type GetChatRouteApiDatasourcesChatsChatUuidGetResponse = GetChatRouteApiDatasourcesChatsChatUuidGetResponses[keyof GetChatRouteApiDatasourcesChatsChatUuidGetResponses];

export type UpdateChatTitleRouteApiDatasourcesChatsChatUuidPutData = {
    body?: never;
    headers?: {
        'x-user-id'?: string | null;
    };
    path: {
        chat_uuid: string;
    };
    query: {
        title: string;
        user_id: string;
    };
    url: '/api/datasources/chats/{chat_uuid}';
};

export type UpdateChatTitleRouteApiDatasourcesChatsChatUuidPutErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type UpdateChatTitleRouteApiDatasourcesChatsChatUuidPutError = UpdateChatTitleRouteApiDatasourcesChatsChatUuidPutErrors[keyof UpdateChatTitleRouteApiDatasourcesChatsChatUuidPutErrors];

export type UpdateChatTitleRouteApiDatasourcesChatsChatUuidPutResponses = {
    /**
     * Successful Response
     */
    200: unknown;
};

export type AddMessageToChatRouteApiDatasourcesChatsChatUuidMessagesPostData = {
    body: MessageCreate;
    headers?: {
        'x-user-id'?: string | null;
    };
    path: {
        chat_uuid: string;
    };
    query: {
        user_id: string;
    };
    url: '/api/datasources/chats/{chat_uuid}/messages';
};

export type AddMessageToChatRouteApiDatasourcesChatsChatUuidMessagesPostErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type AddMessageToChatRouteApiDatasourcesChatsChatUuidMessagesPostError = AddMessageToChatRouteApiDatasourcesChatsChatUuidMessagesPostErrors[keyof AddMessageToChatRouteApiDatasourcesChatsChatUuidMessagesPostErrors];

export type AddMessageToChatRouteApiDatasourcesChatsChatUuidMessagesPostResponses = {
    /**
     * Successful Response
     */
    201: unknown;
};

export type GetDatasourcesRouteApiDatasourcesGetData = {
    body?: never;
    headers?: {
        'x-user-id'?: string | null;
    };
    path?: never;
    query: {
        user_id: string;
    };
    url: '/api/datasources';
};

export type GetDatasourcesRouteApiDatasourcesGetErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type GetDatasourcesRouteApiDatasourcesGetError = GetDatasourcesRouteApiDatasourcesGetErrors[keyof GetDatasourcesRouteApiDatasourcesGetErrors];

export type GetDatasourcesRouteApiDatasourcesGetResponses = {
    /**
     * Successful Response
     */
    200: Array<DatasourceResponse>;
};

export type GetDatasourcesRouteApiDatasourcesGetResponse = GetDatasourcesRouteApiDatasourcesGetResponses[keyof GetDatasourcesRouteApiDatasourcesGetResponses];

export type CreateDatasourceRouteApiDatasourcesPostData = {
    body: DatasourceCreate;
    headers?: {
        'x-user-id'?: string | null;
    };
    path?: never;
    query: {
        user_id: string;
    };
    url: '/api/datasources';
};

export type CreateDatasourceRouteApiDatasourcesPostErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type CreateDatasourceRouteApiDatasourcesPostError = CreateDatasourceRouteApiDatasourcesPostErrors[keyof CreateDatasourceRouteApiDatasourcesPostErrors];

export type CreateDatasourceRouteApiDatasourcesPostResponses = {
    /**
     * Successful Response
     */
    200: unknown;
};

export type DeleteDatasourceRouteApiDatasourcesIdentifierDeleteData = {
    body?: never;
    headers?: {
        'x-user-id'?: string | null;
    };
    path: {
        identifier: string;
    };
    query: {
        user_id: string;
    };
    url: '/api/datasources/{identifier}';
};

export type DeleteDatasourceRouteApiDatasourcesIdentifierDeleteErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type DeleteDatasourceRouteApiDatasourcesIdentifierDeleteError = DeleteDatasourceRouteApiDatasourcesIdentifierDeleteErrors[keyof DeleteDatasourceRouteApiDatasourcesIdentifierDeleteErrors];

export type DeleteDatasourceRouteApiDatasourcesIdentifierDeleteResponses = {
    /**
     * Successful Response
     */
    200: unknown;
};

export type GetDatasourceRouteApiDatasourcesIdentifierGetData = {
    body?: never;
    headers?: {
        'x-user-id'?: string | null;
    };
    path: {
        identifier: string;
    };
    query: {
        user_id: string;
    };
    url: '/api/datasources/{identifier}';
};

export type GetDatasourceRouteApiDatasourcesIdentifierGetErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type GetDatasourceRouteApiDatasourcesIdentifierGetError = GetDatasourceRouteApiDatasourcesIdentifierGetErrors[keyof GetDatasourceRouteApiDatasourcesIdentifierGetErrors];

export type GetDatasourceRouteApiDatasourcesIdentifierGetResponses = {
    /**
     * Successful Response
     */
    200: DatasourceResponse;
};

export type GetDatasourceRouteApiDatasourcesIdentifierGetResponse = GetDatasourceRouteApiDatasourcesIdentifierGetResponses[keyof GetDatasourceRouteApiDatasourcesIdentifierGetResponses];

export type UpdateDatasourceRouteApiDatasourcesIdentifierPatchData = {
    body: DatasourceUpdate;
    headers?: {
        'x-user-id'?: string | null;
    };
    path: {
        identifier: string;
    };
    query: {
        user_id: string;
    };
    url: '/api/datasources/{identifier}';
};

export type UpdateDatasourceRouteApiDatasourcesIdentifierPatchErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type UpdateDatasourceRouteApiDatasourcesIdentifierPatchError = UpdateDatasourceRouteApiDatasourcesIdentifierPatchErrors[keyof UpdateDatasourceRouteApiDatasourcesIdentifierPatchErrors];

export type UpdateDatasourceRouteApiDatasourcesIdentifierPatchResponses = {
    /**
     * Successful Response
     */
    200: unknown;
};

export type ProcessingRouteApiProcessingPostData = {
    body: ProcessingRequest;
    headers?: {
        'x-user-id'?: string | null;
    };
    path?: never;
    query: {
        user_id: string;
    };
    url: '/api/processing';
};

export type ProcessingRouteApiProcessingPostErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type ProcessingRouteApiProcessingPostError = ProcessingRouteApiProcessingPostErrors[keyof ProcessingRouteApiProcessingPostErrors];

export type ProcessingRouteApiProcessingPostResponses = {
    /**
     * Successful Response
     */
    200: ProcessingStatusResponse;
};

export type ProcessingRouteApiProcessingPostResponse = ProcessingRouteApiProcessingPostResponses[keyof ProcessingRouteApiProcessingPostResponses];

export type GetProcessingStatusRouteApiProcessingStatusGetData = {
    body?: never;
    headers?: {
        'x-user-id'?: string | null;
    };
    path?: never;
    query: {
        user_id: string;
    };
    url: '/api/processing/status';
};

export type GetProcessingStatusRouteApiProcessingStatusGetErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type GetProcessingStatusRouteApiProcessingStatusGetError = GetProcessingStatusRouteApiProcessingStatusGetErrors[keyof GetProcessingStatusRouteApiProcessingStatusGetErrors];

export type GetProcessingStatusRouteApiProcessingStatusGetResponses = {
    /**
     * Successful Response
     */
    200: ProcessingStatusResponse;
};

export type GetProcessingStatusRouteApiProcessingStatusGetResponse = GetProcessingStatusRouteApiProcessingStatusGetResponses[keyof GetProcessingStatusRouteApiProcessingStatusGetResponses];

export type GetProcessingStepsRouteApiStacksStepsGetData = {
    body?: never;
    headers?: {
        'x-user-id'?: string | null;
    };
    path?: never;
    query: {
        user_id: string;
    };
    url: '/api/stacks/steps';
};

export type GetProcessingStepsRouteApiStacksStepsGetErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type GetProcessingStepsRouteApiStacksStepsGetError = GetProcessingStepsRouteApiStacksStepsGetErrors[keyof GetProcessingStepsRouteApiStacksStepsGetErrors];

export type GetProcessingStepsRouteApiStacksStepsGetResponses = {
    /**
     * Successful Response
     */
    200: Array<ProcessingStepResponse>;
};

export type GetProcessingStepsRouteApiStacksStepsGetResponse = GetProcessingStepsRouteApiStacksStepsGetResponses[keyof GetProcessingStepsRouteApiStacksStepsGetResponses];

export type GetProcessingStacksRouteApiStacksStacksGetData = {
    body?: never;
    headers?: {
        'x-user-id'?: string | null;
    };
    path?: never;
    query: {
        user_id: string;
    };
    url: '/api/stacks/stacks';
};

export type GetProcessingStacksRouteApiStacksStacksGetErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type GetProcessingStacksRouteApiStacksStacksGetError = GetProcessingStacksRouteApiStacksStacksGetErrors[keyof GetProcessingStacksRouteApiStacksStacksGetErrors];

export type GetProcessingStacksRouteApiStacksStacksGetResponses = {
    /**
     * Successful Response
     */
    200: Array<ProcessingStackResponse>;
};

export type GetProcessingStacksRouteApiStacksStacksGetResponse = GetProcessingStacksRouteApiStacksStacksGetResponses[keyof GetProcessingStacksRouteApiStacksStacksGetResponses];

export type CreateProcessingStackRouteApiStacksStacksPostData = {
    body: ProcessingStackCreate;
    headers?: {
        'x-user-id'?: string | null;
    };
    path?: never;
    query: {
        user_id: string;
    };
    url: '/api/stacks/stacks';
};

export type CreateProcessingStackRouteApiStacksStacksPostErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type CreateProcessingStackRouteApiStacksStacksPostError = CreateProcessingStackRouteApiStacksStacksPostErrors[keyof CreateProcessingStackRouteApiStacksStacksPostErrors];

export type CreateProcessingStackRouteApiStacksStacksPostResponses = {
    /**
     * Successful Response
     */
    200: ProcessingStackResponse;
};

export type CreateProcessingStackRouteApiStacksStacksPostResponse = CreateProcessingStackRouteApiStacksStacksPostResponses[keyof CreateProcessingStackRouteApiStacksStacksPostResponses];

export type DeleteProcessingStackRouteApiStacksStacksStackIdentifierDeleteData = {
    body?: never;
    headers?: {
        'x-user-id'?: string | null;
    };
    path: {
        stack_identifier: string;
    };
    query: {
        user_id: string;
    };
    url: '/api/stacks/stacks/{stack_identifier}';
};

export type DeleteProcessingStackRouteApiStacksStacksStackIdentifierDeleteErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type DeleteProcessingStackRouteApiStacksStacksStackIdentifierDeleteError = DeleteProcessingStackRouteApiStacksStacksStackIdentifierDeleteErrors[keyof DeleteProcessingStackRouteApiStacksStacksStackIdentifierDeleteErrors];

export type DeleteProcessingStackRouteApiStacksStacksStackIdentifierDeleteResponses = {
    /**
     * Successful Response
     */
    200: unknown;
};

export type GetProcessingStackRouteApiStacksStacksStackIdentifierGetData = {
    body?: never;
    headers?: {
        'x-user-id'?: string | null;
    };
    path: {
        stack_identifier: string;
    };
    query: {
        user_id: string;
    };
    url: '/api/stacks/stacks/{stack_identifier}';
};

export type GetProcessingStackRouteApiStacksStacksStackIdentifierGetErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type GetProcessingStackRouteApiStacksStacksStackIdentifierGetError = GetProcessingStackRouteApiStacksStacksStackIdentifierGetErrors[keyof GetProcessingStackRouteApiStacksStacksStackIdentifierGetErrors];

export type GetProcessingStackRouteApiStacksStacksStackIdentifierGetResponses = {
    /**
     * Successful Response
     */
    200: ProcessingStackResponse;
};

export type GetProcessingStackRouteApiStacksStacksStackIdentifierGetResponse = GetProcessingStackRouteApiStacksStacksStackIdentifierGetResponses[keyof GetProcessingStackRouteApiStacksStacksStackIdentifierGetResponses];

export type UpdateProcessingStackRouteApiStacksStacksStackIdentifierPutData = {
    body: ProcessingStackUpdate;
    headers?: {
        'x-user-id'?: string | null;
    };
    path: {
        stack_identifier: string;
    };
    query: {
        user_id: string;
    };
    url: '/api/stacks/stacks/{stack_identifier}';
};

export type UpdateProcessingStackRouteApiStacksStacksStackIdentifierPutErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type UpdateProcessingStackRouteApiStacksStacksStackIdentifierPutError = UpdateProcessingStackRouteApiStacksStacksStackIdentifierPutErrors[keyof UpdateProcessingStackRouteApiStacksStacksStackIdentifierPutErrors];

export type UpdateProcessingStackRouteApiStacksStacksStackIdentifierPutResponses = {
    /**
     * Successful Response
     */
    200: ProcessingStackResponse;
};

export type UpdateProcessingStackRouteApiStacksStacksStackIdentifierPutResponse = UpdateProcessingStackRouteApiStacksStacksStackIdentifierPutResponses[keyof UpdateProcessingStackRouteApiStacksStacksStackIdentifierPutResponses];

export type GetOllamaStatusRouteApiOllamaStatusGetData = {
    body?: never;
    headers?: {
        'x-user-id'?: string | null;
    };
    path?: never;
    query: {
        user_id: string;
    };
    url: '/api/ollama-status';
};

export type GetOllamaStatusRouteApiOllamaStatusGetErrors = {
    /**
     * Validation Error
     */
    422: HttpValidationError;
};

export type GetOllamaStatusRouteApiOllamaStatusGetError = GetOllamaStatusRouteApiOllamaStatusGetErrors[keyof GetOllamaStatusRouteApiOllamaStatusGetErrors];

export type GetOllamaStatusRouteApiOllamaStatusGetResponses = {
    /**
     * Successful Response
     */
    200: OllamaStatusResponse;
};

export type GetOllamaStatusRouteApiOllamaStatusGetResponse = GetOllamaStatusRouteApiOllamaStatusGetResponses[keyof GetOllamaStatusRouteApiOllamaStatusGetResponses];

export type HealthRouteApiHealthGetData = {
    body?: never;
    path?: never;
    query?: never;
    url: '/api/health';
};

export type HealthRouteApiHealthGetResponses = {
    /**
     * Successful Response
     */
    200: string;
};

export type HealthRouteApiHealthGetResponse = HealthRouteApiHealthGetResponses[keyof HealthRouteApiHealthGetResponses];