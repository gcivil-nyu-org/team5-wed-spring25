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


---



# 🛠 Running CleanBites with Docker

To containerize **CleanBites**, follow these steps.

### 1️⃣ Build the Docker Image

Run the following command to build the Docker image:

```sh
docker-compose build
```

---

### 2️⃣ Start the Application in a Docker Container

Run the application in a container:

```sh
docker-compose up -d
```

✅ This starts the backend API, which will be available at `http://localhost:8000`.

---

### 3️⃣ Stopping the Container

To stop the running container:

```sh
docker-compose down
```

✅ This shuts down the application while preserving any persistent data.



---

# 🚀 Updating Docker Container After Repo Changes
## ✅ Summary of Commands

| **Change Type**                           | **Command** |
|-------------------------------------------|-------------|
| Code changes only (Python, HTML, JS, CSS) | `docker-compose down && docker-compose up -d` |
| Dependency updates (`requirements.txt`)   | `docker-compose down && docker-compose build && docker-compose up -d` |
| `Dockerfile` or `docker-compose.yml` changes | `docker-compose down && docker-compose up --build -d` |
| Check logs                                | `docker-compose logs -f` |
| Access running container                  | `docker-compose exec api bash` |




## Notes

- Ensure that your PostgreSQL instance (or AWS RDS database) is running and correctly configured.
- The API is automatically exposed on **port 8000** inside the container.
- If you encounter issues, check logs using:

  ```sh
  docker-compose logs -f
  ```

Enjoy using **CleanBites**! 🚀🎉
