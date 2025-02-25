# CleanBites
---
# CleanBites - Setup Guide

## Prerequisites
Before setting up **CleanBites**, ensure you have the required dependencies installed.

### Install PostgreSQL Development Libraries
CleanBites requires PostgreSQL development libraries to be installed. Use the following command to install them:

```sh
brew install postgresql
```

## Environment Setup

### Windows
For Windows users, activate the **CleanBites** Python environment using:

```sh
.cbenv\Scripts\activate
```

### MacOS
For MacOS users, activate the **CleanBites** Python environment using:

```sh
source .cbenv_os/bin/activate
```

## Ensuring Dependency Consistency
After activating the environment, ensure that the installed dependencies match those in the `requirements.txt` file:

```sh
pip freeze > CleanBites/requirements.txt
```

If there are discrepancies, install the required dependencies:

```sh
pip install -r CleanBites/requirements.txt
```

## Running the Application Locally

### Run the API Instance
Start the API server on port **8000**:

```sh
python manage.py runserver 8000
```

### Run the Frontend Instance
Start the frontend server on port **8001**:

```sh
python manage.py runserver 8001
```

## Notes
- Ensure that your PostgreSQL instance is running and correctly configured.
- Both backend and frontend instances must be running for full application functionality.
- If any issues arise, check for missing dependencies or incorrect environment activation.

Enjoy using **CleanBites**!

