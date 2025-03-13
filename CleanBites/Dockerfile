FROM python:3.8.10-slim

# Install system dependencies for GeoDjango
RUN apt-get update && \
    apt-get install -y gnupg2 && \
    apt-key update && \
    apt-get update && \
    apt-get install -y \
    binutils \
    gdal-bin \
    # PROJ
    libproj-dev \
    # GDAL
    libgdal-dev \
    # GEOS
    libgeos-dev \
    # PostGIS
    libpq-dev \
    # reduce image size
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY ./requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the full Django project, including `CleanBites/`
COPY ./CleanBites /app/CleanBites
COPY ./_frontend /app/_frontend/ 
COPY ./_api /app/_api/ 
COPY ./manage.py /app/

EXPOSE 8000

# Set PYTHONPATH to include `/app`
ENV PYTHONPATH="/app"

# Run Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "CleanBites.wsgi:application"]