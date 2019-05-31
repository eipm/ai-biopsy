FROM python:3.6.8-stretch
#===============================#
# Docker Image Configuration	#
#===============================#
LABEL vendor='Englander Institute for Precision Medicine' \
    description='AI Biopsy' \
    maintainer='als2076@med.cornell.edu' \
    base_image='python' \
    base_image_version='3.6.8-stretch' \
    base_image_SHA256='sha256:ab2670ec57d486f73e49e7352de6a80b6767e3c996c1c0d0c158f17ae6f2d113'

ENV APP_NAME='ai_biopsy' \
    TZ='US/Eastern' \
    AI_BIOPSY_SRC_DIR='/ai_biopsy/src/ai_biopsy_src' \
    PREDICT_DIR='/ai_biopsy/src/ai_biopsy_src/slim'
ENV RESULT_DIR=${AI_BIOPSY}/result \
    PROCESS_DIR=${AI_BIOPSY}/process \
    PYTHONPATH=${PYTHONPATH}:${AI_BIOPSY}:${PREDICT_DIR}

#===================================#
# Install Prerequisites         	#
#===================================#
COPY requirements.txt /${APP_NAME}/requirements.txt
RUN pip install -r /${APP_NAME}/requirements.txt
#===================================#
# Copy Files and set work directory	#
#===================================#
COPY src /${APP_NAME}/src/
WORKDIR /${APP_NAME}
#===================================#
# Startup							#
#===================================#
EXPOSE 80
VOLUME uploads
VOLUME output

HEALTHCHECK --interval=30s --timeout=30s --retries=3 \
    CMD curl -f -k http://0.0.0.0/api/healthcheck || exit 1

CMD python3 /${APP_NAME}/src/main.py