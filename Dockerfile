FROM python:3.11-slim
WORKDIR /app
COPY stress_api.py .
RUN pip install flask flask-cors
EXPOSE 5000
CMD ["python", "stress_api.py"]
