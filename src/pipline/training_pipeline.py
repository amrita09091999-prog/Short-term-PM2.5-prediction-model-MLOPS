import sys
from src.exception import MyException
from src.logger import logging
from src.utils.main_utils import read_json_file

from src.components.data_ingestion import DataIngestion
from src.components.data_validation import DataValidation
from src.components.data_transformation import DataTransformation
from src.components.model_experimenter import ModelTrainer
from src.components.model_experimenter import ModelExperimenter
from src.components.model_evaluation import ModelEvaluation
from src.components.model_pusher import ModelPusher

from src.entity.config_entity import (DataIngestionConfig,
                                        DataValidationConfig,
                                        DataTransformationConfig,
                                        ModelExperimenterConfig,
                                        ModelExperimenterConfig,
                                        ModelEvaluationConfig,
                                        ModelPusherConfig)
                                          
from src.entity.artifact_entity import (DataIngestionArtifact,
                                            DataValidationArtifact,
                                            DataTransformationArtifact,
                                            DataTrainerArtifact,
                                            ModelExperimenterArtifact,
                                            ModelEvaluationArtifact,
                                            ModelPusherArtifact)



class TrainPipeline:
    def __init__(self):
        self.data_ingestion_config = DataIngestionConfig()
        self.data_validation_config = DataValidationConfig()
        self.data_transformation_config = DataTransformationConfig()
        self.model_experimenter_config = ModelExperimenterConfig()
        self.model_evaluation_config = ModelEvaluationConfig()
        self.model_pusher_config = ModelPusherConfig()


    
    def start_data_ingestion(self) -> DataIngestionArtifact:
        """
        This method of TrainPipeline class is responsible for starting data ingestion component
        """
        try:
            logging.info("Entered the start_data_ingestion method of TrainPipeline class")
            logging.info("Getting the data from postgres")
            data_ingestion = DataIngestion(data_ingestion_config=self.data_ingestion_config)
            data_ingestion_artifact = data_ingestion.initiate_data_ingestion()
            logging.info("Got the train_set and test_set from postgres database")
            logging.info("Exited the start_data_ingestion method of TrainPipeline class")
            return data_ingestion_artifact
        except Exception as e:
            raise MyException(e, sys) from e
        
    def start_data_validation(self, data_ingestion_artifact: DataIngestionArtifact) -> DataValidationArtifact:
        """
        This method of TrainPipeline class is responsible for starting data validation component
        """
        logging.info("Entered the start_data_validation method of TrainPipeline class")

        try:
            data_validation = DataValidation(data_ingestion_artifact=data_ingestion_artifact,
                                             data_validation_config=self.data_validation_config
                                             )

            data_validation_artifact = data_validation.initiate_data_validation()

            logging.info("Performed the data validation operation")
            logging.info("Exited the start_data_validation method of TrainPipeline class")

            return data_validation_artifact
        except Exception as e:
            raise MyException(e, sys) from e
        
    def start_data_transformation(self, data_ingestion_artifact: DataIngestionArtifact, data_validation_artifact: DataValidationArtifact) -> DataTransformationArtifact:
        """
        This method of TrainPipeline class is responsible for starting data transformation component
        """
        try:
            data_transformation = DataTransformation(data_ingestion_artifact=data_ingestion_artifact,
                                                     data_transformation_config=self.data_transformation_config,
                                                     data_validation_artifact=data_validation_artifact)
            data_transformation_artifact = data_transformation.initiate_data_transformation()
            return data_transformation_artifact
        except Exception as e:
            raise MyException(e, sys)
        
    def start_model_trainer(self, data_transformation_artifact: DataTransformationArtifact) -> ModelExperimenterArtifact:
        """
        This method of TrainPipeline class is responsible for starting model training
        """
        try:
            model_trainer = ModelTrainer(data_transformation_artifact=data_transformation_artifact,
                                         model_trainer_config=self.model_trainer_config
                                         )
            model_trainer_artifact = model_trainer.initiate_model_trainer()
            return model_trainer_artifact

        except Exception as e:
            raise MyException(e, sys)
    
    def start_model_experimenter(self, data_transformation_artifact: DataTransformationArtifact) -> ModelExperimenterArtifact:
        """
        This method of TrainPipeline class is responsible for model experimentation
        """
        try:
            model_experimenter = ModelExperimenter(data_transformation_artifact=data_transformation_artifact,
                                         model_trainer_config=self.model_experimenter_config
                                         )
            model_experimenter_artifact = model_experimenter.initiate_model_experimenter()
            return model_experimenter_artifact

        except Exception as e:
            raise MyException(e, sys)

    def start_model_evaluation(self, data_transformation_artifact: DataTransformationArtifact,
                               model_trainer_artifact: ModelExperimenterArtifact) -> ModelEvaluationArtifact:
        """
        This method of TrainPipeline class is responsible for starting modle evaluation
        """
        try:
            model_evaluation = ModelEvaluation(model_eval_config=self.model_evaluation_config,
                                            data_transformation_artifact = data_transformation_artifact,
                                               model_experimenter_artifact=model_experimenter_artifact)
            model_evaluation_artifact = model_evaluation.initiate_model_evaluation()
            return model_evaluation_artifact
        except Exception as e:
            raise MyException(e, sys)

    def start_model_pusher(self, model_evaluation_artifact: ModelEvaluationArtifact) -> ModelPusherArtifact:
        """
        This method of TrainPipeline class is responsible for starting model pushing
        """
        try:
            model_pusher = ModelPusher(model_evaluation_artifact=model_evaluation_artifact,
                                       model_pusher_config=self.model_pusher_config
                                       )
            model_pusher_artifact = model_pusher.initiate_model_pusher()
            return model_pusher_artifact
        except Exception as e:
            raise MyException(e, sys)

    def run_pipeline(self,model_experimenter:bool) -> None:
        """
        This method of TrainPipeline class is responsible for running complete pipeline
        """
        try:
            data_ingestion_artifact = self.start_data_ingestion()
            data_validation_artifact = self.start_data_validation(data_ingestion_artifact=data_ingestion_artifact)
            data_transformation_artifact = self.start_data_transformation(
                data_ingestion_artifact=data_ingestion_artifact, data_validation_artifact=data_validation_artifact)
            if model_experimendet==1:
                model_trainer_artifact = self.start_model_experimenter(data_transformation_artifact= data_transformation_artifact)
            else:
                model = "pull model from s3 bucket and then re use it here"
                model_trainer_artifact = self.model_trainer(model, data_transformation_artifact)

            model_evaluation_artifact = self.start_model_evaluation(data_transformation_artifact=data_transformation_artifact,
                                                                     model_experimenter_artifact=model_trainer_artifact)
            if not model_evaluation_artifact.is_model_accepted:
                logging.info(f"Model not accepted.")
                return None
            model_pusher_artifact = self.start_model_pusher(model_evaluation_artifact=model_evaluation_artifact)
            
        except Exception as e:
            raise MyException(e, sys)