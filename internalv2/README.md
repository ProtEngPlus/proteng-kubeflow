## Run Local
```bash
cd internal
uvicorn cmd.example_microservice:app --host 0.0.0.0 --port 8080
```


## Docker
### build docker image
same dockerfile, just change the build arg
```bash
docker build -t example-service -f ./internalv2/dockerfiles/microservice.Dockerfile --build-arg="SERVICE_NAME=<example-service>" ./internalv2
```
or
```bash
cd internalv2
docker build -t example-service -f ./dockerfiles/microservice.Dockerfile --build-arg="SERVICE_NAME=<example-service>" .
```
### run docker
- change port to the specific port in dockerfile
```
docker run -d --name example-service -p 8080:8080 example-service
```
