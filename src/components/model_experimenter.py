import sys
import importlib
import itertools
from typing import Tuple

import numpy as np
import mlflow
import mlflow.sklearn
import dagshub

from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from src.exception import MyException
from src.logger import logging
from src.utils.main_utils import (
    load_numpy_array_data,
    read_yaml_file,
    save_object,
    write_json_file
)
from src.entity.config_entity import ModelExperimenterConfig
from src.entity.artifact_entity import (
    DataTransformationArtifact,
    ModelExperimenterArtifact,
    RegressionMetricArtifact
)
from src.constants import (
    PARAMETERS_FILE_PATH,
    DAGSHUB_REPO_OWNER,
    DAGSHUB_REPO_NAME,
    MLFLOW_EXPERIMENT_NAME,
    BASE_ADJUSTED_R2_SCORE
)


class ModelExperimenter:
    def __init__(
        self,
        data_transformation_artifact: DataTransformationArtifact,
        model_experimenter_config: ModelExperimenterConfig,
    ):
        self.data_transformation_artifact = data_transformation_artifact
        self.model_experimenter_config = model_experimenter_config

        self._parameters_config = read_yaml_file(PARAMETERS_FILE_PATH)

        self.repo_owner = DAGSHUB_REPO_OWNER
        self.repo_name = DAGSHUB_REPO_NAME
        self.experiment_name = MLFLOW_EXPERIMENT_NAME

    def get_model_experimentation(self,train_arr:np.array,test_arr:np.array) -> Tuple[object, RegressionMetricArtifact]:
        try:
            logging.info("Starting Model Experimentation with MLflow")

            X_train, y_train = train_arr[:, :-1], train_arr[:, -1]
            X_test, y_test = test_arr[:, :-1], test_arr[:, -1]

            n_features = X_test.shape[1]
            n_samples = X_test.shape[0]

            # ---------------- Best Model Trackers ----------------
            best_adj_r2 = -float("inf")
            best_model = None
            best_model_name = None
            best_params = None
            best_model_r2 = None
            best_model_rmse = None
            best_model_mae = None

            # ---------------- DagsHub + MLflow Setup ----------------
            print(self.repo_owner)
            print(self.repo_name)
            dagshub.init(repo_owner='amrita09091999-prog', repo_name='Short-term-PM2.5-prediction-model-MLOPS', mlflow=True)
            mlflow.set_tracking_uri(
               "https://dagshub.com/amrita09091999-prog/Short-term-PM2.5-prediction-model-MLOPS.mlflow"
            )
            print(f"https://dagshub.com/{self.repo_owner}/{self.repo_name}.mlflow")
            mlflow.set_experiment(self.experiment_name)

            # ---------------- Parent Run ----------------
            with mlflow.start_run(run_name="MODEL_TRAINING"):
                logging.info("logging the primary artifacts")

                mlflow.log_param("train_samples", X_train.shape[0])
                mlflow.log_param("test_samples", X_test.shape[0])
                mlflow.log_param("n_features", n_features)
                mlflow.log_param("n_samples", n_samples)

                # ---------------- Model Loop ----------------
                for model_type, model_cfg in self._parameters_config["models"].items():

                    with mlflow.start_run(run_name=model_type, nested=True):

                        module = importlib.import_module(model_cfg["module"])
                        model_class = getattr(module, model_cfg["class"])
                        param_grid = model_cfg["params"]

                        param_keys = list(param_grid.keys())
                        param_combinations = list(
                            itertools.product(*param_grid.values())
                        )

                        for i, values in enumerate(param_combinations):

                            params = dict(zip(param_keys, values))
                            # if "random_state" in model_class().get_params():
                            #     params["random_state"] = 42
                            logging.info(f"Experiement runnning for model - {model_type}, combination - {i}")
                            logging.info(f"params used  - {params}")
                            with mlflow.start_run(
                                run_name=f"{model_type}_run_{i}",
                                nested=True,
                            ):
                                model = model_class(**params)
                                model.fit(X_train, y_train)

                                y_pred = model.predict(X_test)

                                r2 = r2_score(y_test, y_pred)
                                mae = mean_absolute_error(y_test, y_pred)
                                rmse = np.sqrt(mean_squared_error(y_test, y_pred))

                                # Safe Adjusted R²
                                if n_samples > n_features + 1:
                                    adj_r2 = 1 - (
                                        (1 - r2)
                                        * (n_samples - 1)
                                        / (n_samples - n_features - 1)
                                    )
                                else:
                                    adj_r2 = r2

                                mlflow.log_params(params)
                                mlflow.log_metric("r2", r2)
                                mlflow.log_metric("adj_r2", adj_r2)
                                mlflow.log_metric("mae", mae)
                                mlflow.log_metric("rmse", rmse)

                                if adj_r2 > best_adj_r2:
                                    best_adj_r2 = adj_r2
                                    best_model = model
                                    best_model_name = model_type
                                    best_params = params
                                    best_model_r2 = r2
                                    best_model_rmse = rmse
                                    best_model_mae = mae

                # ---------------- Log Best Model ----------------
                logging.info("logging the best model parameters and artifacts")
                with mlflow.start_run(run_name="BEST_MODEL", nested=True):

                    mlflow.log_param("best_model_type", best_model_name)
                    mlflow.log_params(best_params)
                    mlflow.log_metric("best_adj_r2", best_adj_r2)
                    mlflow.log_metric("best_r2", best_model_r2)
                    mlflow.log_metric("best_rmse", best_model_rmse)
                    mlflow.log_metric("best_mae", best_model_mae)

                    mlflow.sklearn.log_model(
                        best_model,
                        artifact_path="model",
                        registered_model_name="PM2.5-Best-Regressor",
                    )

            metric_artifact = RegressionMetricArtifact(
                best_model_name=best_model_name,
                judgement_criterion = 'Adjusted R2',
                best_params = best_params,
                best_model_r2=best_model_r2,
                best_adj_r2=best_adj_r2,
                best_model_mae=best_model_mae,
                best_model_rmse=best_model_rmse,
            )

            return best_model, metric_artifact

        except Exception as e:
            raise MyException(e, sys)
    
    def initiate_model_experimenter(self) -> ModelExperimenterArtifact:
        logging.info("Entered initiate_model_model method of ModelExperimenter class")
        """
        Method Name :   initiate_model_experimenter
        Description :   This function initiates the model experimentation steps
        
        Output      :   Returns model experimenter artifact
        On Failure  :   Write an exception log and then raise an exception
        """
        # ---------------- Load Data ----------------
        try:
            train_arr = load_numpy_array_data(
                self.data_transformation_artifact.transformed_train_file_path
            )
            test_arr = load_numpy_array_data(
                self.data_transformation_artifact.transformed_test_file_path
            )
            logging.info("train-test data loaded")
                
            trained_model, metric_artifact = self.get_model_experimentation(train_arr = train_arr, test_arr = test_arr)
            logging.info("Model object and artifact loaded.")

            if metric_artifact.best_adj_r2<BASE_ADJUSTED_R2_SCORE:
                logging.info("No model found with score above the base adjusted R2 score")
                raise Exception("No model found with score above the base adjusted R2 score")

            logging.info("Saving the final best model as performace is better than the base adjusted R2 score.")
            save_object(self.model_experimenter_config.trained_model_file_path,trained_model)
            write_json_file(self.model_experimenter_config.trained_model_best_params_file_path,metric_artifact.best_params)
            best_metrics = {
                'best_model':metric_artifact.best_model_name,
                'judgement_criteria':metric_artifact.judgement_criterion,
                'best_adj_r2':metric_artifact.best_adj_r2,
                'best_r2':metric_artifact.best_model_r2,
                'best_mae':metric_artifact.best_model_mae,
                'best_rmse':metric_artifact.best_model_rmse
            }
            write_json_file(self.model_experimenter_config.trained_model_best_metrics_file_path,best_metrics)
            model_trainer_artifact = ModelTrainerArtifact(
                    trained_model_file_path=self.model_experimenter_config.trained_model_file_path,
                    metric_artifact=metric_artifact,
                )
            logging.info(f"Model trainer artifact: {model_trainer_artifact}")
            
            return model_trainer_artifact
        
        except Exception as e:
            raise MyException(e, sys) from e


