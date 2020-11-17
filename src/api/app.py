import os
import random
from flask import Flask, jsonify, flash, request, redirect, url_for,send_from_directory,make_response
from werkzeug.utils import secure_filename
from flask_cors import CORS
import uuid as myuuid
import cv2
import glob
import datetime
import numpy as np
import png, pydicom
from ast import literal_eval

# Relative Imports
from api.version import api_version
from api.model import Model

# Define Directories
MODELS = [
    Model('Cancer_Benign', 'Model1_Cancer_Benign', 'cancer', 'benign'),
    Model('High_Low', 'Model2_High_Low', 'high', 'low')]

ALLOWED_EXTENSIONS = set(['jpg', 'png', 'tif', 'tiff', 'dcm'])

static_file_dir = os.path.join(os.getcwd(), 'src/static')
upload_dir = os.path.join(os.getcwd(), 'uploads')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
app.config['CORS_HEADERS'] = 'Content-Type'
CORS(app)

users_dict = literal_eval(os.environ['USERS_DICT'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods = ['GET'])
def serve_index_page():
    return send_from_directory(static_file_dir, 'index.html')

@app.route('/<path:path>', methods = ['GET'])
def serve_assets(path):
    return send_from_directory(static_file_dir, path)

@app.route('/api', methods = ['GET'])
def api_swagger():
    return "Swagger API coming soon..."

@app.route('/api/healthcheck', methods = ['GET'])
def healthcheck():
    return jsonify({'status':'Healthy', 'version':api_version()})

@app.route('/login', methods = ['GET'])
def serve_login_page():
    return send_from_directory(static_file_dir, 'login.html')

@app.route('/api/login', methods = ['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if username and users_dict[username] == password:
        response = make_response()
        uuid = str(myuuid.uuid4())
        response.set_cookie('ai-biopsy-auth', uuid, max_age=3600)
        return response
    return jsonify({}), 401

@app.route('/api/upload', methods = ['POST'])
def upload_image():
    auth_token = None
    auth_header = request.headers.get('Authorization')
    print(auth_header)
    if auth_header is None or auth_header.split(" ")[1] is None:
        flash('No Authorization header')
        return jsonify({}), 401

    # check if the post request has the file part
    if 'image' not in request.files:
        flash('No file part')
        return redirect(request.url)

    # 1. Create request directory
    request_id = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
    request_dir = (os.path.join(upload_dir, request_id))
    if not os.path.exists(request_dir):
        os.makedirs(request_dir)

    response_dict = {}
    images_dict = {}
    # For each uploaded image
    for image in request.files.getlist('image'):
        # 2. Save Image
        filename = secure_filename(image.filename)
        image.save(os.path.join(request_dir, filename))

        images_dict[filename] = image.filename

    # 3. Normalize images to jpeg format
    for image in glob.glob(os.path.join(request_dir, '*.*')):
        filename = os.path.splitext(image)[0]
        if os.path.splitext(image)[1] == '.dcm':
            ds = pydicom.dcmread(image)
            shape = ds.pixel_array.shape

            # Convert to float to avoid overflow or underflow losses.
            image_2d = ds.pixel_array.astype(float)

            # Rescaling grey scale between 0-255
            image_2d_scaled = (np.maximum(image_2d,0) / image_2d.max()) * 255.0

            # Convert to uint
            image_2d_scaled = np.uint8(image_2d_scaled)

            # Write the PNG file
            with open(os.path.join(request_dir, filename) + '.png' , 'wb') as png_file:
                w = png.Writer(shape[1], shape[0], greyscale=True)
                w.write(png_file, image_2d_scaled)
        else:
            img = cv2.imread(image)
            os.remove(image)
            filename = '%s.png' % filename
            cv2.imwrite(os.path.join(request_dir, filename), img)

    for model in MODELS:
        model_result = model.get_model_results(request_id, request_dir)
        write_model_results_in_response(response_dict, model, model_result, images_dict)

    return jsonify(response_dict), 200

def write_model_results_in_response(response_dict, model, model_result, images_dict):
    for image_result in model_result:
        filepath = os.path.basename(image_result[0])
        filename = os.path.splitext(filepath)[0]
        ext = os.path.splitext(filepath)[1]
        for saved_file_name, initital_file_name in images_dict.items():
            if saved_file_name.lower() in [("{}.{}".format(filename, ext)).lower() for ext in ALLOWED_EXTENSIONS]:
                obj = {}
                if initital_file_name in response_dict:
                    obj = response_dict[initital_file_name]
                else:
                    response_dict[initital_file_name] = obj
                obj[model.first_value_name] = image_result[1]
                obj[model.second_value_name] = image_result[2]
                break

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
