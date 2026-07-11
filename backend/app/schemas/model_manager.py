from pydantic import BaseModel

class ModelFeatures(BaseModel):
    numeric: list[str]
    categorical: list[str]
    all_input_columns: list[str]

class ModelMetadata(BaseModel):
    model_purpose: str
    target: str
    algorithm: str
    target_transform: str | None = None
    features: ModelFeatures
    important_note: str | None = None

class ModelArtifact(BaseModel):
    artifact_id: str
    folder_name: str
    is_active: bool
    metadata: ModelMetadata

class AvailableModelsResponse(BaseModel):
    active_artifact_id: str
    models: list[ModelArtifact]

class SwitchModelRequest(BaseModel):
    artifact_id: str

class SwitchModelResponse(BaseModel):
    message: str
    active_artifact_id: str
