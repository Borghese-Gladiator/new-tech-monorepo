## Created on Oct 1st, 2024

# Fast API Hugging Face
Hugging Face is a platform for machine learning community to collaborate on models, datasets, and applications. Hugging Face Transformers is an open-source library that provides access to thousands of pre-trained Transformer models. The Hugging Face Hub is a platform with over 900k models, 200k datasets, and 300k demos.

# Notes
First time using Hugging Face

Steps
- download model
- write FastAPI to expose model
- build Docker image to simplify shipping

## Local Setup
Python

Docker
- `docker build -t fastapi-sentiment-analysis .`


# Notes
- `localhost` - hostname that referes to local machine. Human-readable alias for `127.0.0.1`
- `127.0.0.1` - Special IP address (called Loopback Address) that refers to the local machine. It enables communication with local machine without going through network. It is not accessible from other devices
- `0.0.0.0` - Special IP address that means "all IPv4 addresses on the local machine." When a server binds to 0.0.0.0, it listens to all network interfaces - both internal (`127.0.0.1`) and external (local network IP, like `192.168.x.x`).
