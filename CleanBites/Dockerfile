FROM python:3.7.9-slim

# set working directory in the container
WORKDIR /app

# # Install system dependencies
# RUN apt-get update && apt-get install -y \
#     postgresql-client \
#     && rm -rf /var/lib/apt/lists/*

# # Upgrade pip
# RUN pip install --upgrade pip

# copy requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy project code into the container
COPY . .

# # collect static files
# RUN python manage.py collectstatic --noinput

# run app
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "CleanBites.wsgi:application"]