FROM python:3.9

WORKDIR /app

# Install system dependencies for PyTorch
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch from its index
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install other packages from PyPI
RUN pip install --no-cache-dir flask flask-cors numpy pandas scikit-learn joblib

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]