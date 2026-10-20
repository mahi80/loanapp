# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies.
COPY requirements.txt requirements-governance.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ACP governance SDK (private mahi80/rbi). Pass a GitHub token as a BuildKit secret
# so it never lands in an image layer:
#   echo ghp_xxx > .github_token && DOCKER_BUILDKIT=1 docker compose build app
# ACP_GOVERNANCE=required makes the build fail without the token (use for prod images);
# the default `auto` builds an ungoverned image and says so loudly.
ARG ACP_GOVERNANCE=auto
RUN --mount=type=secret,id=github_token,required=false \
    if [ -s /run/secrets/github_token ]; then \
      git config --global url."https://$(cat /run/secrets/github_token)@github.com/".insteadOf "https://github.com/" \
      && pip install --no-cache-dir -r requirements-governance.txt \
      && rm -f /root/.gitconfig \
      && python -c "import acp; print('acp-sdk', acp.__version__, 'installed')"; \
    elif [ "$ACP_GOVERNANCE" = "required" ]; then \
      echo "ERROR: ACP_GOVERNANCE=required but no github_token secret was provided" >&2; exit 1; \
    else \
      echo "WARNING: no github_token secret — building WITHOUT acp-sdk (graph runs ungoverned)" >&2; \
    fi

# Application code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
