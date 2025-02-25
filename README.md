# CleanBites
---
# CleanBites - Setup Guide

## Prerequisites
Before setting up **CleanBites**, ensure you have the required dependencies installed.

### Install PostgreSQL Development Libraries
CleanBites requires PostgreSQL development libraries to be installed.

#### MacOS
Use the following command to install them:

```sh
brew install postgresql
```

#### Windows
For Windows, download and install the PostgreSQL development libraries from the official PostgreSQL website:

1. Visit [PostgreSQL Downloads](https://www.postgresql.org/download/)
2. Select your Windows version and download the installer.
3. Follow the installation steps, ensuring the development libraries are included.

After installation, verify that PostgreSQL is installed correctly by checking its configuration:

```sh
pg_config --version
```

or

```sh
postgres --version
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



