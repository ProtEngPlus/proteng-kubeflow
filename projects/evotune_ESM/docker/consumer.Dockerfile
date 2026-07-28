FROM python:3.11.7-slim

WORKDIR /consumer

COPY projects/evotune_ESM .

RUN mkdir pkg

COPY /pkg /consumer/pkg

RUN pip install --no-cache-dir numpy==1.26.4
RUN pip install pydantic

RUN pip install --upgrade pydantic

RUN pip install --no-cache-dir --upgrade -r pkg/common/requirements.txt
RUN pip install --no-cache-dir --default-timeout=100 --upgrade -r requirements.txt

CMD ["python3", "consumer.py"]

