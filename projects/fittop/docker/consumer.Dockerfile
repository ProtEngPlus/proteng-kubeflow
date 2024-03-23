FROM python:3.11.7-slim

WORKDIR /consumer

COPY projects/fittop .

RUN mkdir pkg

COPY /pkg /consumer/pkg

RUN pip install --no-cache-dir --upgrade -r pkg/common/requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

CMD ["python3", "consumer.py"]
