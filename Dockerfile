FROM dataloopai/dtlpy-agent:cpu.py3.8.opencv4.7

RUN pip install --user \
    shapely \
    scikit-learn