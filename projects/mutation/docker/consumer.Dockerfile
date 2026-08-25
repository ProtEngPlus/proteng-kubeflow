FROM python:3.11.7-slim

WORKDIR /consumer

RUN apt-get update && apt-get install -y --no-install-recommends \
    procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY projects/mutation .

RUN mkdir pkg

COPY /pkg /consumer/pkg

RUN pip install --no-cache-dir numpy==1.26.4
RUN pip install pydantic

RUN pip install --upgrade pydantic

RUN pip install --no-cache-dir --upgrade -r pkg/common/requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt
RUN pip install --no-cache-dir numpy==1.26.4

CMD ["python3", "consumer.py"]
