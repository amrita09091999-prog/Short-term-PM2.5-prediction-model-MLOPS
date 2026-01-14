from src.entity.config_entity import ModelEvaluationConfig
from src.entity.artifact_entity import ModelExperimenterArtifact, DataTransformationArtifact, ModelEvaluationArtifact
from src.exception import MyException
from sklearn.metrics import r2_score
from src.logger import logging
from src.utils.main_utils import load_object,load_numpy_array_data
import sys
import pandas as pd
from typing import Optional
from src.entity.s3_estimator import Proj1Estimator
from dataclasses import dataclass

@dataclass
class EvaluateModelResponse:
    trained_model_adj_r2_score: float
    best_model_adj_r2_score: float
    is_model_accepted: bool
    difference: float


class ModelEvaluation:

    def __init__(self, model_eval_config: ModelEvaluationConfig, data_transformation_artifact: DataTransformationArtifact,
                 model_experimenter_artifact: ModelExperimenterArtifact):
        try:
            self.model_eval_config = model_eval_config
            self.data_transformation_artifact = data_transformation_artifact
            self.model_experimenter_artifact = model_experimenter_artifact
        except Exception as e:
            raise MyException(e, sys) from e

    def get_best_model(self) -> Optional[Proj1Estimator]:
        """
        Method Name :   get_best_model
        Description :   This function is used to get model from production stage.
        
        Output      :   Returns model object if available in s3 storage
        On Failure  :   Write an exception log and then raise an exception
        """
        try:
            bucket_name = self.model_eval_config.bucket_name
            model_path=self.model_eval_config.s3_model_key_path
            proj1_estimator = Proj1Estimator(bucket_name=bucket_name,
                                               model_path=model_path)

            if proj1_estimator.is_model_present(model_path=model_path):
                return proj1_estimator
            return None
        except Exception as e:
            raise  MyException(e,sys)
        
    def evaluate_model(self) -> EvaluateModelResponse:
        """
        Method Name :   evaluate_model
        Description :   This function is used to evaluate trained model 
                        with production model and choose best model 
        
        Output      :   Returns bool value based on validation results
        On Failure  :   Write an exception log and then raise an exception
        """
        try:
            test_arr = load_numpy_array_data(
                self.data_transformation_artifact.transformed_test_file_path
            )
            x,y = test_arr[:, :-1], test_arr[:, -1]

            logging.info("Test data loaded and now transforming it for prediction...")


            trained_model = load_object(file_path=self.model_experimenter_artifact.trained_model_file_path)
            logging.info("Trained model loaded/exists.")
            trained_model_adj_r2_score = self.model_experimenter_artifact.metric_artifact.best_model_r2
            logging.info(f"Adjuted R2 Score for this model: {trained_model_adj_r2_score}")

            best_model_adj_r2_score=None
            best_model = self.get_best_model()
            if best_model is not None:
                logging.info(f"Computing adj_R2_Score for production model..")
                y_hat_best_model = best_model.predict(x)
                r2 = r2_score(y, y_hat_best_model)
                n_features = x.shape[1]
                n_samples = x.shape[0]
                best_model_adj_r2_score = 1 - (
                             (1 - r2)
                            * (n_samples - 1)
                            / (n_samples - n_features - 1)
                        )
                logging.info(f"adj_r2_Score-Production Model: {adj_r2}, adj_r2_Score-New Trained Model: {trained_model_adj_r2_score}")
            
            tmp_best_model_score = 0 if best_model_adj_r2_score is None else best_model_adj_r2_score
            result = EvaluateModelResponse(trained_model_adj_r2_score=trained_model_adj_r2_score,
                                           best_model_adj_r2_score=best_model_adj_r2_score,
                                           is_model_accepted=trained_model_adj_r2_score > tmp_best_model_score,
                                           difference=trained_model_adj_r2_score - tmp_best_model_score
                                           )
            logging.info(f"Result: {result}")
            return result

        except Exception as e:
            raise MyException(e, sys)

    def initiate_model_evaluation(self) -> ModelEvaluationArtifact:
        """
        Method Name :   initiate_model_evaluation
        Description :   This function is used to initiate all steps of the model evaluation
        
        Output      :   Returns model evaluation artifact
        On Failure  :   Write an exception log and then raise an exception
        """  
        try:
            print("------------------------------------------------------------------------------------------------")
            logging.info("Initialized Model Evaluation Component.")
            evaluate_model_response = self.evaluate_model()
            s3_model_path = self.model_eval_config.s3_model_key_path

            model_evaluation_artifact = ModelEvaluationArtifact(
                is_model_accepted=evaluate_model_response.is_model_accepted,
                s3_model_path=s3_model_path,
                trained_model_path=self.model_experimenter_artifact.trained_model_file_path,
                changed_adj_r2=evaluate_model_response.difference)

            logging.info(f"Model evaluation artifact: {model_evaluation_artifact}")
            return model_evaluation_artifact
        except Exception as e:
            raise MyException(e, sys) from e