FROM python:3.7-alpine
WORKDIR /ieddit
ENV PYTHONPATH /ieddit
ENV FLASK_APP app.py
ENV FLASK_RUN_HOST 0.0.0.0
ENV FLASK_RUN_PORT=80
RUN apk add --no-cache gcc musl-dev linux-headers postgresql-dev
# PIL dependencies
RUN apk add build-base python-dev py-pip jpeg-dev zlib-dev
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
COPY config.py ./
RUN ["python3", "create_db.py"]
CMD ["flask", "run"]
