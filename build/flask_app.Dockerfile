FROM python:3.8

WORKDIR /app

COPY requirements.txt requirements.txt
COPY flask_app.py flask_app.py
COPY clients clients
COPY utils utils

RUN pip install --upgrade pip
RUN pip install --upgrade -r /app/requirements.txt

ENTRYPOINT ["flask", "--app", "flask_app", "--debug", "run", "--host", "0.0.0.0"]
