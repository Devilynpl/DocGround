FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml requirements.txt* README.md ./
COPY src/ ./src/

# Step 1: Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Step 2: Install CPU-only torch BEFORE sentence-transformers so pip
# resolves torch from the CPU wheel index instead of pulling 2.5 GB CUDA libs.
RUN pip install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu \
        torch torchvision

# Step 3: Install the package and all remaining deps
RUN pip install --no-cache-dir -e .

COPY data/processed/ ./data/processed/
COPY DocGroundAI_logo.jpg ./

EXPOSE 8501
EXPOSE 8502

HEALTHCHECK --interval=20s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "src/docground/ui/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
