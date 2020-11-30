import tensorflow as tf
slim = tf.contrib.slim
import sys
import os
#import matplotlib.pyplot as plt
import numpy as np
import os
from nets import inception
from preprocessing import inception_preprocessing
from os import listdir
from os.path import isfile, join
from os import walk
import cv2
import cam_utils
import GuidedReLu
#os.environ['CUDA_VISIBLE_DEVICES'] = '' #Uncomment this line to run prediction on CPU.
#os.environ['CUDA_VISIBLE_DEVICES'] = '' #Uncomment this line to run prediction on CPU.
session = tf.Session()

def get_test_images(mypath):
	return [mypath + '/' + f for f in listdir(mypath) if isfile(join(mypath, f)) and f.find('.png') != -1]


def transform_img_fn(path_list, cam):
	'''
	transform the image for prediction or cam
	args:
	path_list: the list of test images
	cam: whether to excecute cam
	returns transofmed images
	'''
	out = []
	for f in path_list:
	    image_raw = tf.image.decode_jpeg(open(f,'rb').read(), channels=3)
	    image = inception_preprocessing.preprocess_image(image_raw, image_size, image_size, is_training=False, is_CAM = cam)
	    out.append(image)
	return session.run([out])[0]

def get_weights(filename, return_tensors, print_tensors):
	return cam_utils.return_tensors_in_checkpoint_file(filename, return_tensors, print_tensors)


if __name__ == '__main__':


	if len(sys.argv) != 9:
		print("The script needs eight arguments.")
		print("The first argument should be the CNN architecture: v1, v3 or inception_resnet2")
		print("The second argument should be the directory of trained model.")
		print("The third argument should be directory of test images.")
		print("The  fourth argument should be output directory for the CAMmed image")
		print("The  fifth argument should be number of classes.")
		print("The sixth argument should be the name of ckpt file for the trained model you want to use")
		print("The seventh argument should be the name of parameter for the last softmax layer stored in the ckpt file")
		print("The eighth argument should be the name of the activation layer assigned in the architecture you used")
		exit()
	deep_lerning_architecture = sys.argv[1]
	train_dir = sys.argv[2]
	test_path = sys.argv[3]
	output_cam = sys.argv[4]
	nb_classes = int(sys.argv[5])
	model_path = train_dir + sys.argv[6]
	parameter_name = sys.argv[7]
	layer_name = sys.argv[8]

	if deep_lerning_architecture == "v1" or deep_lerning_architecture == "V1":
		image_size = 224
	else:
		if deep_lerning_architecture == "v3" or deep_lerning_architecture == "V3" or deep_lerning_architecture == "resv2" or deep_lerning_architecture == "inception_resnet2":
			image_size = 299
		else:
			print("The selected architecture is not correct.")
			exit()


	print('Start to read images!')
	image_list = get_test_images(test_path)
	labels_cam, labels_uncam = cam_utils.get_cam_images_label(test_path, output_cam, False)
	labels_GC, labels_GGC = cam_utils.get_cam_images_label(test_path, output_cam)
	processed_images = tf.placeholder(tf.float32, shape=(None, image_size, image_size, 3))

	if deep_lerning_architecture == "v1" or deep_lerning_architecture == "V1":
		with slim.arg_scope(inception.inception_v1_arg_scope()):
			logits, activations = inception.inception_v1(processed_images, num_classes=nb_classes, is_training=False)
	else:
		if deep_lerning_architecture == "v3" or deep_lerning_architecture == "V3":
			with slim.arg_scope(inception.inception_v3_arg_scope()):
				logits, activations = inception.inception_v3(processed_images, num_classes=nb_classes, is_training=False)
		else:
			if deep_lerning_architecture == "resv2" or deep_lerning_architecture == "inception_resnet2":
				with slim.arg_scope(inception.inception_resnet_v2_arg_scope()):
					logits, activations = inception.inception_resnet_v2(processed_images, num_classes=nb_classes, is_training=False)


	def grad_CAM_fn(images):
		return session.run(gradient_GrC, feed_dict={processed_images:images})

	def guided_BP(images):
		return session.run(gradient_BP, feed_dict = {processed_images: images})

	def conv_output_fn(images):
		return session.run(conv_output, feed_dict = {processed_images: images})


	conv_output = activations[layer_name]
	probabilities = tf.nn.softmax(logits)
	yc_idx = tf.one_hot(np.ones((len(image_list),1)), nb_classes)
	yc_idx = tf.squeeze(yc_idx)
	loss = yc_idx*probabilities
	reduced_loss = tf.reduce_sum(loss, axis = 1)
	gradient_GrC = tf.gradients(reduced_loss, conv_output)[0]
	#computing the gradient of choosed convlutional layer with respect to the assigned class

	

	g = tf.get_default_graph()
	with g.gradient_override_map({'Relu': 'GuidedRelu'}):
		#print("costshape", loss.shape)
		gradient_BP = tf.gradients(reduced_loss, processed_images)[0]
	#computing the backpropagation


	checkpoint_path = tf.train.latest_checkpoint(train_dir)
	init_fn = slim.assign_from_checkpoint_fn(checkpoint_path,slim.get_variables_to_restore())
	init_fn(session)
	print('Start to transform images!')

	images = transform_img_fn(image_list, False)
	images_cam = transform_img_fn(image_list, True)


	print('Start generating cam!')
	conv_output = conv_output_fn(images)

	grad_GrC_value = grad_CAM_fn(images)

	grad_BP_value= guided_BP(images)


	class_weights_dict = get_weights(model_path, True, False)
	class_weights = class_weights_dict[parameter_name]


	shape = (image_size, image_size)

	#cam_utils.GGCAM(grad_BP_value, grad_GrC_value, conv_output, shape, labels_GC, images_cam, labels_GGC)
	cam_utils.CAM(conv_output, class_weights, shape, labels_cam, images_cam, labels_uncam)

	print("# Finished, Total number of pictures: %d" % len(image_list))

