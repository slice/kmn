FROM python:latest

WORKDIR /app
ADD . /app

RUN pip install -r requirements.txt

CMD ["python", "launcher.py"]
