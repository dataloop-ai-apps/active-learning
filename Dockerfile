FROM dataloopai/dtlpy-agent:cpu.py3.8.opencv.Dockerfile

RUN pip install --user \
    shapely \
    scikit-learn