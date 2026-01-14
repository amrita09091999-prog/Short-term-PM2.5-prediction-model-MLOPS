from dataclasses import dataclass

@dataclass
class DataIngestionArtifact:
    trained_file_path:str
    test_file_path:str

@dataclass
class DataValidationArtifact:
    validation_status:bool
    message: str
    validation_report_file_path: str

@dataclass
class DataTransformationArtifact:
    transformed_train_file_path:str
    transformed_test_file_path:str

@dataclass
class RegressionMetricArtifact:
    best_model_name: str
    judgement_criteria:str
    best_params: dict
    best_adj_r2:float
    best_model_r2:float
    best_model_mae:float
    best_model_rmse:float

@dataclass
class ModelExperimenterArtifact:
    trained_model_file_path:str 
    metric_artifact:RegressionMetricArtifact

@dataclass
class ModelEvaluationArtifact:
    is_model_accepted:bool
    changed_adj_r2:float
    s3_model_path:str 
    trained_model_path:str

@dataclass
class ModelPusherArtifact:
    bucket_name:str
    s3_model_path:str