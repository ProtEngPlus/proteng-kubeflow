# proteng-kubeflow

## Project structure
<pre>
.
├── compose                             # docker compose folder
│   └── compose.yml
│
└── internal
    ├── common                          # common folder for every microservice
    │   └── utils.py 
    └── example-microservice
        ├── Dockerfile                  # <b>dockerfile</b> for 'example' microservice
        ├── main.py                     # <b>entrypoint</b> for dockerfile
        ├── requirements.txt            # <b>requirements</b> for 'example' microservice
        └── src                         # src for 'example' microservice
            ├── service                 # main service folder ( contain all logics in service )
            │   └── train.py           
            └── data                    # store data
                └── example_data.txt          
</pre>
## Docker
### build docker image
```
docker build -t example-service -f ./internal/example-microservice/Dockerfile ./internal
```
### run docker
- change port to the specific port in dockerfile
```
docker run -d --name example-service -p 8080:8080 example-service
```
