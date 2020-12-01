import os
import csv
import logging
from typing import List, Type
from api.model_process_result import ModelProcessResult

OUTPUT_DIR = 'output'
MODELS_DIR = 'src/ai_biopsy_src'
CAM_DIR = 'CAM'

class Model:
    def __init__(self, name, path, first_value_name, second_value_name):
        self.__name = name
        self.__path = path
        self.__first_value_name = first_value_name
        self.__second_value_name = second_value_name

    @property
    def name(self):
      return self.__name

    @property
    def path(self):
        return self.__path

    @property
    def first_value_name(self):
        return self.__first_value_name

    @property
    def second_value_name(self):
        return self.__second_value_name

    @property
    def __output_dir(self):
        return os.path.join(os.getcwd(), OUTPUT_DIR)

    @property
    def __models_dir(self):
        return os.path.join(os.getcwd(), MODELS_DIR)

    def get_model_results(self, request_id: str, request_dir: str) -> Type[ModelProcessResult]:
        request_output_dir = self.__get_request_output_folder_path(request_id)
        output_file = os.path.join(request_output_dir, self.__get_output_file())
        cam_output_folder = self.__get_cam_output_folder_path(request_output_dir)
        self.__run_tensorflow(request_dir, request_output_dir)
        predictions = self.__get_results_from_output_file(output_file)
        images = [os.path.join(cam_output_folder , x) for x in os.listdir(cam_output_folder) if x.endswith('_CAM.png')]
        return ModelProcessResult(predictions, images)

    def __get_results_from_output_file(self, output_file):
        return list(csv.reader(open(output_file, 'r', encoding='utf8'), delimiter='\t'))

    def __get_model_folder_path(self) -> str:
        return os.path.join(self.__models_dir, self.path)

    def __get_output_file(self) -> str:
        return f'{self.name}.txt'

    def __get_request_output_folder_path(self, request_id: str) -> str:
        dir = os.path.join(self.__output_dir, request_id)
        if not os.path.exists(dir):
            os.makedirs(dir)

        return dir

    def __get_cam_output_folder_path(self, request_output_dir: str) -> str:
        dir = os.path.join(request_output_dir, f'{self.name}_{CAM_DIR}')
        if not os.path.exists(dir):
            os.makedirs(dir)

        return dir

    def __run_tensorflow(self, request_dir: str, request_output_dir: str) -> None:
        model_folder_path = self.__get_model_folder_path()
        predict_dir = os.path.join(model_folder_path, 'slim')
        result_dir = os.path.join(model_folder_path, 'result')
        output_file = os.path.join(request_output_dir, self.__get_output_file())
        cam_output_folder = self.__get_cam_output_folder_path(request_output_dir)

        python_command = 'python3 ' + os.path.join(predict_dir, 'predict.py') + ' v1 ' + result_dir + ' ' + request_dir + ' ' + output_file + ' 2'
        print(python_command)
        os.system(python_command)

        python_command = 'python3 ' + os.path.join(predict_dir, 'CAM.py') + ' v1 ' + result_dir + '/ ' + request_dir + ' ' + cam_output_folder + ' 2  model.ckpt-10000 InceptionV1/Logits/Conv2d_0c_1x1/weights Mixed_5c'
        print(python_command)
        os.system(python_command)
