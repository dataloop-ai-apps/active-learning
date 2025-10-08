FROM hub.dataloop.ai/dtlpy-runner-images/cpu:python3.11_opencv

RUN pip install --user \
    shapely \
    scikit-learn