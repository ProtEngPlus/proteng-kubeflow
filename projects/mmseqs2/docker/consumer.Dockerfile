FROM python:3.11.7-slim

WORKDIR /consumer
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    build-essential \
    gcc \
    libffi-dev \
    libssl-dev \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://mmseqs.com/latest/mmseqs-linux-sse41.tar.gz && \
    tar xvf mmseqs-linux-sse41.tar.gz && \
    mv mmseqs/bin/mmseqs /usr/local/bin && \
    rm -rf mmseqs mmseqs-linux-sse41.tar.gz

COPY projects/mmseqs2 .

RUN mkdir pkg

COPY /pkg /consumer/pkg

RUN pip install --upgrade pip

RUN pip install --no-cache-dir numpy==1.26.4
RUN pip install pydantic

RUN pip install --upgrade pydantic

RUN pip install --no-cache-dir --upgrade -r pkg/common/requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

CMD ["python3", "consumer.py"]
