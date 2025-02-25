# CleanBites - Setup Guide

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
