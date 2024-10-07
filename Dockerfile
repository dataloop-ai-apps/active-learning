FROM dataloopai/dtlpy-agent:cpu

RUN pip install --user \
    shapely \
    scikit-learn