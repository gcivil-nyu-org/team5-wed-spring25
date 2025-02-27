FROM python:3.7.9-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY ../requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the full Django project, including `CleanBites/`
COPY ../CleanBites /app/CleanBites
COPY ../_frontend /app/_frontend/ 
COPY ../_api /app/_api/ 
COPY ../manage.py /app/

EXPOSE 8001

# Set PYTHONPATH to include `/app`
ENV PYTHONPATH="/app"

# Run Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8001", "CleanBites.wsgi:application"]
