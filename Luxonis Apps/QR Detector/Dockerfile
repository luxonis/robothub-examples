FROM ghcr.io/luxonis/robothub-app-v2:2024.117.2129-rvc2-regular

WORKDIR /app
COPY requirements.txt /app/

# Set non-interactive installation environment.
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    g++ \
    cmake \
    git \
    make \
    libopencv-dev \
    python3-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Update setuptools and wheel for Python dependencies
RUN pip install --upgrade pip setuptools wheel

# Clone the zxing-cpp repository
RUN git clone https://github.com/zxing-cpp/zxing-cpp.git --single-branch --depth 1

# Configure the project with CMake
RUN cmake -S zxing-cpp -B zxing-cpp.release -DCMAKE_BUILD_TYPE=Release

# Build the project
RUN cmake --build zxing-cpp.release -j8 --config Release

# Install pybind11 via pip to help with Python bindings
RUN pip install pybind11

# Install Python dependencies
# RUN pip install --no-cache-dir -r requirements.txt
