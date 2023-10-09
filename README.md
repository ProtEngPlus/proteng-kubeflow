# proteng-kubeflow

## Project structure
<pre>
.
├── compose
│   └── compose.yml
│
├── dockerfiles
│   └── example-microservice
│       ├── Dockerfile          # <b>dockerfile</b> for 'example' microservice
│       └── requirements.txt    # <b>requirements</b> for 'example' microservice
│
└── src/[language]              # seperate each language in src folder
    ├── example-microservice    # src folder for 'example' microservice
    │   ├── main.py             # <b>entrypoint</b> for dockerfile
    │   └── train.py          
    └── utils.py                # file for common utils function that every service commonly use
</pre>
