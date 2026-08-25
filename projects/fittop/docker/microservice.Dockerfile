FROM python:3.11.7-slim

WORKDIR /microservice

COPY projects/fittop .

RUN mkdir pkg

COPY /pkg /microservice/pkg

RUN pip install --no-cache-dir --upgrade -r pkg/common/requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt
RUN pip install --no-cache-dir numpy==1.26.4

CMD ["uvicorn", "microservice:app", "--host", "0.0.0.0", "--port", "8080"]
