# Use Amazon Linux 2023 as the base image
FROM amazonlinux:2023

# Install system dependencies
RUN dnf update -y && \
    dnf install -y \
    gcc gcc-c++ make \
    wget tar unzip \
    sqlite sqlite-devel \
    postgresql-devel \
    libpq-devel \
    expat expat-devel \
    util-linux \
    && dnf clean all

ENV CONDA_OVERRIDE_CUDA="true"
ENV CONDA_NO_CUDA="1"
ENV CONDA_MAX_MEMORY=500
ENV CONDA_INSTALL_THREADS=1

# Install Miniconda for GIS tools
# RUN wget -O Miniconda3.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
#     chmod +x Miniconda3.sh && \
#     ./Miniconda3.sh -b -p /opt/conda && \
#     rm Miniconda3.sh
# Replace with this code if running locally on Mac
RUN wget -O Miniconda3.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh && \
    chmod +x Miniconda3.sh && \
    ./Miniconda3.sh -b -p /opt/conda && \
    rm Miniconda3.sh

# Add Conda to PATH
ENV PATH="/opt/conda/bin:$PATH"

# Create a lightweight Conda environment and install Python 3.9
RUN conda create -y -n cleanbites-env python=3.9 && \
    conda clean --all

# Activate the Conda environment
ENV CONDA_DEFAULT_ENV=cleanbites-env
ENV PATH="/opt/conda/envs/cleanbites-env/bin:$PATH"

# Install specific versions of GDAL, GEOS, and PROJ inside the Conda environment
RUN conda install -y -c conda-forge \
    gdal \
    psycopg2 \
    && conda clean --all

# Set working directory
WORKDIR /app

# Copy requirements first
COPY ./requirements.txt .
COPY ./utils.py /app/


# Install Python dependencies using Conda's Python 3.9
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Django project
COPY ./CleanBites /app/CleanBites
COPY ./_frontend /app/_frontend
COPY ./_api /app/_api
COPY ./manage.py /app/

COPY ./staticfiles /app/staticfiles
# Need to collect static files for frontend
RUN mkdir -p /app/static
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Set PYTHONPATH
ENV PYTHONPATH="/app"

# Run Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "CleanBites.wsgi:application"]