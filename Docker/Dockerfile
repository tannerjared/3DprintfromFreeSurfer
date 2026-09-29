FROM python:3.10-slim-bookworm

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libxrender1 \
        libxtst6 && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir \
    numpy \
    numpy-stl \
    pymeshlab==2025.7.post1 \
    vtk==9.7.0

COPY 3Dprintprep.py /app/3Dprintprep.py

ENTRYPOINT ["python3", "/app/3Dprintprep.py"]
