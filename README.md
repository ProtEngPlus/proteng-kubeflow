# proteng-kubeflow

## Project structure
<pre>
.
├── compose                             # docker compose folder
│   └── compose.yml
│
└── proteng-microservice
    └── example-microservice
        ├── Dockerfile                  # <b>dockerfile</b> for 'example' microservice
        ├── main.py                     # <b>entrypoint</b> for dockerfile
        ├── requirements.txt            # <b>requirements</b> for 'example' microservice
        └── src                         # src for 'example' microservice
            ├── service                 # main service folder ( contain all logics in service )
            │   └── train.py           
            ├── data                    # store data
            │   └── example_data.txt          
            └── utils                   # utils folder
                └── utils.py 
</pre>
