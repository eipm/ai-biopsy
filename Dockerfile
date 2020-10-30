FROM python:3.7.9-buster
#===============================#
# Docker Image Configuration	#
#===============================#
LABEL org.opencontainers.image.source='https://github.com/eipm/ai-biopsy' \
    vendor='Englander Institute for Precision Medicine' \
    description='AI Biopsy' \
    maintainer='als2076@med.cornell.edu'

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
