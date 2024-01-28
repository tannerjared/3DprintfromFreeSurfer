# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /usr/src/app
COPY . /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libgl1-mesa-glx libglib2.0-0 libxrender1 libxtst6 && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python packages
# If you have a requirements.txt file, uncomment the next line and make sure the file is in the context of the build
# COPY requirements.txt ./
# RUN pip install --no-cache-dir -r requirements.txt

# Install individual Python packages if you don't have a requirements.txt
RUN pip3 install --no-cache-dir numpy numpy-stl pymeshlab==2022.2.post4 vtk

# Copy the 3Dprintprep.py script into the container
COPY 3Dprintprep.py .

# Run 3Dprintprep.py when the container launches
ENTRYPOINT ["python3", "/app/3Dprintprep.py"]
