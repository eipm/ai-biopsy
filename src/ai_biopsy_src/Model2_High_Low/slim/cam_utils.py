
# Copyright 2016 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================


"""A simple script for inspect checkpoint files."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import re
import sys

import numpy as np

from tensorflow.python import pywrap_tensorflow
from tensorflow.python.platform import app
from tensorflow.python.platform import flags

import os
from os import listdir
from os.path import isfile, join
from os import walk

import tensorflow as tf
import cv2

FLAGS = None



def _count_total_params(reader, count_exclude_pattern=""):
  """Count total number of variables."""
  var_to_shape_map = reader.get_variable_to_shape_map()

  # Filter out tensors that we don't want to count
  if count_exclude_pattern:
    regex_pattern = re.compile(count_exclude_pattern)
    new_var_to_shape_map = {}
    exclude_num_tensors = 0
    exclude_num_params = 0
    for v in var_to_shape_map:
      if regex_pattern.search(v):
        exclude_num_tensors += 1
        exclude_num_params += np.prod(var_to_shape_map[v])
      else:
        new_var_to_shape_map[v] = var_to_shape_map[v]
    var_to_shape_map = new_var_to_shape_map
    print("# Excluding %d tensors (%d params) that match %s when counting." % (
        exclude_num_tensors, exclude_num_params, count_exclude_pattern))

  var_sizes = [np.prod(var_to_shape_map[v]) for v in var_to_shape_map]
  return np.sum(var_sizes, dtype=int)


def return_tensors_in_checkpoint_file(file_name, return_tensors, print_tensors):
  """Prints tensors in a checkpoint file.
  If no `tensor_name` is provided, prints the tensor names and shapes
  in the checkpoint file.
  If `tensor_name` is provided, prints the content of the tensor.
  Args:
    file_name: Name of the checkpoint file.
    return_tensors: Boolean for whether to return all tensors
    print_tensors: Boolean whether to print all_tensors
  """
  dict_weights = {}
  try:
    reader = pywrap_tensorflow.NewCheckpointReader(file_name)
    if return_tensors:
      var_to_shape_map = reader.get_variable_to_shape_map()
      for key in sorted(var_to_shape_map):
          dict_weights[key] = reader.get_tensor(key)
          if print_tensors:
              print("tensor_name: ", key)
              #print(reader.get_tensor(key))
    print("# Total number of params: %d" % _count_total_params(
        reader, count_exclude_pattern=""))
          # Count total number of parameters and print
    return dict_weights
  except Exception as e:  # pylint: disable=broad-except
    print(str(e))
    if "corrupted compressed block contents" in str(e):
      print("It's likely that your checkpoint file has been compressed "
            "with SNAPPY.")
    if ("Data loss" in str(e) and
        any(e in file_name for e in [".index", ".meta", ".data"])):
      proposed_file = ".".join(file_name.split(".")[0:-1])
      v2_file_error_template = """
It's likely that this is a V2 checkpoint and you need to provide the filename
*prefix*.  Try removing the '.' and extension.  Try:
inspect checkpoint --file_name = {}"""
      print(v2_file_error_template.format(proposed_file))



def deprocess_image(x):
    '''
    Same normalization as in:
    https://github.com/fchollet/keras/blob/master/examples/conv_filter_visualization.py
    '''
    if np.ndim(x) > 3:
        x = np.squeeze(x)
    # normalize tensor: center on 0., ensure std is 0.1
    x -= x.mean()
    x /= (x.std() + 1e-5)
    x *= 0.1

    # clip to [0, 1]
    x += 0.5
    x = np.clip(x, 0, 1)

    # convert to RGB array
    x *= 255
    x = np.clip(x, 0, 255).astype('uint8')
    return x
  

def normalize(x):
    # utility function to normalize a tensor by its L2 norm
    return x / (np.sqrt(np.mean(np.square(x))) + 1e-5)

def ReLU(x):
    # utility function to apply relu to an numpy array
    return (x) * (x > 0)



def color_enhancement(image):
  # unitility function to apply color enhancement to guided-cam
  hsvImg = cv2.cvtColor(image,cv2.COLOR_BGR2HSV)

  #multiple by a factor to change the saturation
  hsvImg[...,1] = hsvImg[...,1]*2.0

  #multiple by a factor of less than 1 to reduce the brightness 
  hsvImg[...,2] = hsvImg[...,2]*0.6

  image=cv2.cvtColor(hsvImg,cv2.COLOR_HSV2BGR)
  return image

def get_cam_images_label(test_path, cam_path, GGC = True):
  #unitily functions to create label list for cam and (guided) grad-cam
  labels = [f for f in os.listdir(test_path) if f.endswith('.png')]
  labels = [l.replace(".png", "") for l in labels]
  if GGC: 
    labels_cam = [cam_path+"/"+l + "_GCAM.png" for l in labels]
    labels_uncam = [cam_path+"/"+l + "_GGCAM.png" for l in labels]
  else:
    labels_cam = [cam_path+"/"+l + "_CAM.png" for l in labels]

    labels_uncam = [cam_path+"/"+l + "_nonCAM.png" for l in labels]
  return labels_cam, labels_uncam


def CAM_single(conv_output, class_weights, shape, output_path_cam, original_img, output_path_orig):
  '''
  generate CAMed output image for a single image
  args:
  conv_output: the output of the last convolutional layer, waited to be average pooled
  class_weights: weight of softmax layer
  shape: the shape of original image
  output_path: out path of generated camed_images
  orignal_img: the original image of current item
  output_path_orig: the output path for the original image

  returns:
  an numpy array representing the cam weights
  '''

  cam = np.zeros(dtype = np.float32, shape = conv_output.shape[0:2])
  #creating holders for cam weights, the order of shape is in accordance with inception V1

  class_weights = np.squeeze(class_weights)
  #squeeze the class weights into 2 dimensional vectors

  for i in range(class_weights.shape[1]):
    weights_idx = 0
    weights = np.squeeze(class_weights[:,i])
    for weight in weights:
      print(cam.shape, weight.shape, conv_output[:, :, 0].shape)
      cam += weight*conv_output[:,:,weights_idx]
      #using global average pooling to generate the cam filter


  cam = cam - np.min(cam)
  cam /= np.max(cam)
  cam = cv2.resize(cam, shape)
  #nomalization

  heatmap = cv2.applyColorMap(np.uint8(255*cam), cv2.COLORMAP_JET)
  #heatmap[np.where(cam < 0.18)] = 0
  img = heatmap*0.5 + 255*original_img*0.9
  #generating heat map, 0.5 and 0.9 adjustable

  cv2.imwrite(output_path_cam, img)
  #print(output_path_cam)
  cv2.imwrite(output_path_orig, 255*original_img)
  #also generate the original image of the same size for reference
  return cam


def grad_cam_single(gradient_GrC, conv_output):
  '''
  generate grad-CAMed output image for a single image
  args:
  conv_output: the output of the last convolutional layer, waited to be average pooled
  class_weights: weight of softmax layer
  shape: the shape of original image
  output_path: out path of generated camed_images
  orignal_img: the original image of current item
  output_path_orig: the output path for the original image

  returns:
  an numpy array representing the cam weights
  '''
  grad_cam = np.zeros(dtype = np.float32, shape = conv_output.shape[0:2])
  weights = np.mean(gradient_GrC, axis = (1,2))
  weights = np.squeeze(weights)
  weights_idx = 0
  for weight in weights:
    grad_cam += weight*conv_output[:,:,weights_idx]

  grad_cam = ReLU(grad_cam)
  return grad_cam


def guided_grad_cam_single(grad_BP, grad_GrC, conv_output, shape, output_path_gc, original_img, output_path_ggc):
  grad_cam = grad_cam_single(grad_GrC, conv_output)
  grad_cam = grad_cam - np.min(grad_cam)
  grad_cam = grad_cam/np.max(grad_cam)
  grad_cam = cv2.resize(grad_cam, shape)
  
  grad_BP = grad_BP - np.min(grad_BP)
  grad_BP = grad_BP/np.max(grad_BP)

 
  heatmap = cv2.applyColorMap(np.uint8(grad_cam*255), cv2.COLORMAP_JET)

  #heatmap[np.where(grad_cam < 0.6)] = 0
  img_grad_cam = heatmap*0.5 + 255*original_img*0.9


  cv2.imwrite(output_path_gc, img_grad_cam)

  grad_cam = cv2.cvtColor(grad_cam, cv2.COLOR_GRAY2RGB)
  guided_grad_cam = np.zeros(grad_BP.shape)

  guided_grad_cam = grad_BP*grad_cam
  #point wise product of guided backpropagation and grad-cam
  guided_grad_cam = deprocess_image(guided_grad_cam)
  
  guided_grad_cam = guided_grad_cam * 0.6 + original_img * 0.4 * 255
  guided_grad_cam = np.clip(guided_grad_cam, 0, 255).astype('uint8')

  cv2.imwrite(output_path_ggc, color_enhancement(guided_grad_cam))

  

def CAM(conv_output_list, class_weights, shape, output_path_cam, original_imgs, output_path_orig):
  '''applying cam for a list of images and store them in designated directory'''
  #print(len(conv_output_list), len(class_weights), len(shape), len(output_path_cam), len(original_imgs), len(output_path_orig))
  for i in range(len(conv_output_list)):
   
    CAM_single(conv_output_list[i], class_weights, shape, output_path_cam[i], original_imgs[i], output_path_orig[i])


def GGCAM(grad_BP, grad_GrC, conv_output, shape, output_path_gc, original_imgs, output_path_ggc):
  '''applying guided grad-cam for a list of images and store them in designated directory'''
  #print(len(conv_output_list), len(class_weights), len(shape), len(output_path_cam), len(original_imgs), len(output_path_orig))
  for i in range(len(grad_BP)):
    
    guided_grad_cam_single(grad_BP[i], grad_GrC[i], conv_output[i], shape, output_path_gc[i], original_imgs[i], output_path_ggc[i])



    

if __name__ == '__main__':
  if len(sys.argv) != 2:
    print("The please add the address ckpt file you want to inspect")
  else:
    return_tensors_in_checkpoint_file(sys.argv[1], True, True)

