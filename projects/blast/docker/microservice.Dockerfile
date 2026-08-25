FROM python:3.11.7-slim

WORKDIR /microservice

COPY projects/blast .

RUN mkdir pkg

COPY /pkg /microservice/pkg

RUN pip install --upgrade pip
RUN pip install --no-cache-dir numpy==1.26.4

RUN pip install --no-cache-dir --upgrade -r pkg/common/requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

CMD ["uvicorn", "microservice:app", "--host", "0.0.0.0", "--port", "8080"]
