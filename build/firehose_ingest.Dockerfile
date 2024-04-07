FROM python:3.8

WORKDIR /app

COPY requirements.txt requirements.txt
COPY firehose_ingest.py firehose_ingest.py
COPY labeler.py labeler.py
COPY clients clients
COPY utils utils

RUN pip install --upgrade pip
RUN pip install --upgrade -r /app/requirements.txt

ENTRYPOINT ["python", "-um", "firehose_ingest"]
