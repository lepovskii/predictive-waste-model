export interface ModelFeatures {
    numeric: string[];
    categorical: string[];
    all_input_columns: string[];
}

export interface ModelMetadata {
    model_purpose: string;
    target: string;
    algorithm: string;
    target_transform?: string;
    features: ModelFeatures;
    important_note?: string;
}

export interface ModelArtifact {
    artifact_id: string;
    folder_name: string;
    is_active: boolean;
    metadata: ModelMetadata;
}

export interface AvailableModelsResponse {
    active_artifact_id: string;
    models: ModelArtifact[];
}

export interface SwitchModelResponse {
    message: string;
    active_artifact_id: string;
}
