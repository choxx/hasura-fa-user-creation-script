FROM python:latest as development

WORKDIR /usr/app/src

COPY load.py .
COPY requirements.txt .

RUN pip install -r requirements.txt

ENTRYPOINT [ "python", "./load.py"]