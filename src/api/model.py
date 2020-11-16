import os
import csv
import logging

OUTPUT_DIR = 'output'
MODELS_DIR = 'src/ai_biopsy_src'

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

    def get_model_results(self, request_id, request_dir):
        output_file = self.__get_output_file_path(request_id)
        self.__run_tensorflow(request_dir, output_file) 
        return list(csv.reader(open(output_file, 'r', encoding='utf8'), delimiter='\t'))

    def __get_model_folder_path(self):
        return os.path.join(self.__models_dir, self.path)

    def __get_output_file_path(self, request_id):
        request_output_dir = os.path.join(self.__output_dir, request_id)
        if not os.path.exists(request_output_dir):
          os.makedirs(request_output_dir)

        output_filename = f'{self.name}.txt'
        filePath = os.path.join(request_output_dir, output_filename)
        # # Creates a new file
        # with open(filePath, 'w') as fp:
        #     pass
        return filePath

    def __run_tensorflow(self, request_dir, output_file):
        model_folder_path = self.__get_model_folder_path()
        predict_dir = os.path.join(model_folder_path, 'slim')
        result_dir = os.path.join(model_folder_path, 'result')

        python_command='python3 ' + os.path.join(predict_dir, 'predict.py') + ' v1 ' + result_dir + ' ' + request_dir + ' ' + output_file + ' 2'
        print(python_command)
        os.system(python_command)
