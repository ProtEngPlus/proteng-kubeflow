## Docker
### build docker image
same dockerfile, just change the build arg
```
docker build -t example-service -f ./internalv2/dockerfiles/microservice.Dockerfile --build-arg="SERVICE_NAME=<example-service>" ./internalv2
```
### run docker
- change port to the specific port in dockerfile
```
docker run -d --name example-service -p 8080:8080 example-service
```