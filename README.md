# AI Biopsy

Source code for manuscript:

"***Biopsy-free prediction of prostate cancer aggressiveness using deep learning and radiology imaging***"

[Posted on medRxiv](https://www.medrxiv.org/content/10.1101/2019.12.16.19015057v1), 12/19/2019: https://doi.org/10.1101/2019.12.16.19015057

[![medRxiv badge](https://zenodo.org/badge/doi/10.1101/2019.12.16.19015057.svg)](https://doi.org/10.1101/2019.12.16.19015057) ⬅️ read the preprint here

<p align="center">
    <img src="docs/images/logo.png" width="256">
</p>

[![Actions Status](https://github.com/eipm/ai-biopsy/workflows/Docker/badge.svg)](https://github.com/eipm/ai-biopsy/actions) [![Github](https://img.shields.io/badge/github-1.2.1-green?style=flat&logo=github)](https://github.com/eipm/ai-biopsy) [![EIPM Docker Hub](https://img.shields.io/badge/EIPM%20docker%20hub-1.2.1-blue?style=flat&logo=docker)](https://hub.docker.com/repository/docker/eipm/ai-biopsy) [![GitHub Container Registry](https://img.shields.io/badge/GitHub%20Container%20Registry-1.2.1-blue?style=flat&logo=docker)](https://github.com/orgs/eipm/packages/container/package/ai-biopsy) [![Python 3.7.9](https://img.shields.io/badge/python-3.7.9-blue.svg)](https://www.python.org/downloads/release/python-379/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## AI Biopsy Requirements

- Docker. Get it from [here](https://www.docker.com/).
- `process` and `result` folders from ML training (Not included in this repository).

## Running AI Biopsy

To run the AI-biopsy framework please follow these steps:

1. Install TensorFlow. Follow the instructions from [here](https://www.tensorflow.org/install/).

2. Pre-trained Models of CNN architectures should be downloaded from the "Pre-trained Models" part of [https://github.com/wenwei202/terngrad/tree/master/slim#pre-trained-models](https://github.com/wenwei202/terngrad/tree/master/slim#pre-trained-models) and be located in your machine (e.g. GitHub_AI-biopsy/scripts/slim/run/checkpoint). The files for pre-trained models are available under the column named "Checkpoint".

3. Divide the images with the original size into two or more classes based on the aim of classification (e.g., discrimination of aggressive and non-aggressive). 85% of images in each class will be selected as Train set (train and validation) and 15% for Test set.

4. `_NUM_CLASSES` should be set in embryo.py (this script is located in `AI-biopsy/scripts/slim/datasets`).

5. Run the `convert.py` (it is located in the `AI-biopsy/scripts` directory) to allocate the suitable percentage of images to train and validation sets. The `convert.py` needs three arguments including:
    - the address of images for training,
    - the address of where the result will be located, and
    - the percentage of validation images for the training step:

    ```bash
    python convert.py ../Images/train process/ 0
    ```

    - Keep the percentage of validation images as 0 because we set 15% for validation inside the code
    - It will save converted .tf records in the "process" directory.

6. The Inception-V1 architecture should be run on the Train set images from the "AI-biopsy/scripts/slim" directory. First got the the following directory: AI-biopsy /scripts/slim. Then open load_inception_v1.sh located in "run/" directory and edit PRETRAINED_CHECKPOINT_DIR, TRAIN_DIR, and DATASET_DIR addresses. See the load_inception_v1.sh, for instance. Then, run the following command in shell script:

    `$ ./run/load_inception_v1.sh`

    - If you got the bash error like permission denied, run the following line in your shell:  

    ```bash
    chmod 777 load_inception_v1.sh
    ```

    - Each script in slim dataset should be run separately based on the selected architecture. The slim folder contains some sub-folders.
    - You can set up the parameters of each architectures in “run” sub-folder. For example you can set the architecture in a way to run from scratch or trained for the last or all layer. Also you can set the batch size or the number of maximum steps.
    - see the result folder at scripts/result as the result of running the above script.
    - Note that the flag for --clone_on_cpu is set to "True". If you are going to use GPUs you should change this flag to "False".

7. The trained algorithms should be tested using test set images. In folder " AI-biopsy /scripts/slim", predict.py loads a trained model on provided images. This code get 5 arguments:

    ```bash
    python predict.py v1 ../result/ ../../Images/test output.txt 2
    ```

    - v1 = inception-v1, ../Images/test = the address of test set images, out.txt = the output result file, 2 = number of classes
    - You can see output.txt in "GitHub_AI-biopsy/scripts/slim", for example.

8. The accuracy can be measured using accuracy measurement codes ("acc.py") in "useful" folder. The output.txt file should be in the same folder that you are running acc.py. Then run the following code:

    ```bash
    python acc.py
    ```

* https://kwotsin.github.io/tech/2017/02/11/transfer-learning.html

## Running AI Biopsy using Docker

### Load Environment Variables

```bash
DOCKER_CONTAINER_NAME=ai_biopsy
AI_BIOPSY_PORT=3002
OUTPUT_DIR=$PWD/output/
UPLOAD_DIR=$PWD/uploads/
PROCESS1_DIR=$PWD/src/ai_biopsy_src/Model1_Cancer_Benign/process/
RESULT1_DIR=$PWD/src/ai_biopsy_src/Model1_Cancer_Benign/result/
PROCESS2_DIR=$PWD/src/ai_biopsy_src/Model2_High_Low/process/
RESULT2_DIR=$PWD/src/ai_biopsy_src/Model2_High_Low/result/
AI_BIOPSY_TAG=latest
```

### Run Docker Container

```bash
docker run -d --name ${DOCKER_CONTAINER_NAME} \
--restart on-failure:5 \
-p ${AI_BIOPSY_PORT}:80 \
-v ${OUTPUT_DIR}:/ai_biopsy/output \
-v ${UPLOAD_DIR}:/ai_biopsy/uploads \
-v ${PROCESS1_DIR}:/ai_biopsy/src/ai_biopsy_src/Model1_Cancer_Benign/process/:ro \
-v ${RESULT1_DIR}:/ai_biopsy/src/ai_biopsy_src/Model1_Cancer_Benign/result/:ro \
-v ${PROCESS2_DIR}:/ai_biopsy/src/ai_biopsy_src/Model2_High_Low/process/:ro \
-v ${RESULT2_DIR}:/ai_biopsy/src/ai_biopsy_src/Model2_High_Low/result/:ro \
--env USERS_DICT="{ 'user1': 'password1', 'user2': 'password2' }" \
eipm/ai-biopsy:${AI_BIOPSY_TAG}
```

Where:

- **${DOCKER_CONTAINER_NAME}**: The AI Biopsy docker container name.
- **${AI_BIOPSY_PORT}**: The ai_biopsy host port.
- **${OUTPUT_DIR}**: Where AI Biopsy image classification logs will be written.
- **${UPLOAD_DIR}**: Where AI Biopsy image will be saved.
- **${PROCESS_DIR}**: Required directory from ML training.
- **${RESULT_DIR}**: Required directory from ML training.
- **${USERS_DICT}**: The users credentials dictionary to authenticate.
- **${AI_BIOPSY_TAG}**: The AI Biopsy Version to deploy.
`
