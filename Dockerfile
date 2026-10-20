# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies. acp-sdk is installed from the private mahi80/rbi repo:
# pass a token as a BuildKit secret so it never lands in an image layer —
#   DOCKER_BUILDKIT=1 docker build --secret id=github_token,src=$HOME/.github_token .
#   (compose: `secrets: [github_token]` on the build, see docker-compose.yml)
COPY requirements.txt .
RUN --mount=type=secret,id=github_token,required=false \
    if [ -s /run/secrets/github_token ]; then \
      git config --global url."https://$(cat /run/secrets/github_token)@github.com/".insteadOf "https://github.com/"; \
    fi \
    && pip install --no-cache-dir -r requirements.txt \
    && rm -f /root/.gitconfig

# Application code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
