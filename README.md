# proteng-kubeflow

This repository is basically a place that create _**microservices docker image**_ for ML pipeline

PS. at first **_we_**(the first proteng students group to do this project) plan to use kubeflow for our pipeline (hence the name "kubeflow"). But later on into the project, we decided not to use it(kubeflow) and you can find more info on [_devops_ _repository_](https://github.com/ProtEngPlus/manual-guides-2023/tree/main/devops)

## Table of Contents
- [Project Structure](#project-structure)
- [How to run](#running-in-local)
- [How to add new microservice](#how-to-add-new-microservice)
- [How to use microservice in ML pipeline](#how-to-use-microservice-in-production)

## Project Structure

This is a mono-repo project. Each project in the `projects` folder is isolated from each other (Each project is a `microservice` that will be used for ML Pipeline).
The `pkg` folder contains the common services/files that is shared across microservices. 

<pre>
.
├── pkg                                 # shared package that all modules can use
│   ├── common
│   |   ├── rabbitmq.py 
│   |   └── requirements.txt            # each pkg module will have their dependencies declared
|   └── some-library
|       ├── some_module.py
│       └── requirements.txt
| 
└── projects
    |
    └── example
        ├── docker                      # each projects can have multiple <b>Dockerfile</b>s for different type of apps to build
        |   └── microservice.Dockerfile  
        |                               # the <b>entrypoint</b> files to run. projects can have multiple entrypoints, with each one defines 1 app.
        ├── microservice.py             # entrypoint that use FastAPI (first version)
        ├── consumer.py                 # entrypoint that use RabbitMQ (second version) <b>(currently use this version)</b>
        |  
        ├── requirements.txt            # <b>dependencies</b> for 'example' microservice
        └── src                         # src for 'example' microservice
            ├── service                 # main source code folder for that project ( contain all logics in service )
            │   └── train.py
            ├── const.py                # constant for 'example' microservice
            ├── logger.py               # import logger for logging in microservice
            └── data                  
                └── example_data.txt          
</pre>

## Running In Local

### create `.env` file with these info

- **Caution!! please remove below info as soon as possible for good practices and keep it somewhere safe!!**
```
PROJECT_ID="cucpbioinfo"
PRIVATE_KEY_ID="ebc8cba8ab4f978a050bcb9fbafe20f358e6ce9f"
PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCe6FaYArm/yBf5\nSO7jJVWRCNZ3evIeZ7df9Un6YtB2kelst7KGO/caGFM1IP8qdTDXZq0CTYP/6HY3\nhicVl7GEBZJyIILLVisLaqjOqNkfkHbgAEsqJr5aDL2Y8zVf2aRiM6rbrr5g+x6k\nMilGm7Jzn5HzoXwf0wD2gRxz4mkDeTmmDkeLD/Bb+RQi4ZSVYdBa+9vhkHDWxmI0\nIiRhg0QjFTqSKvKbIxOImIJz7LaTd+1asMpZTdB/bxkzZNr4Deuc7cpWoEQ6k3M/\nAzzfmkqgYAlCDiPCiSKNcVY3YvBSZce+9VBtWvlM0ggNl7sjjtw1dJEn+4ojaFP3\npCPEDBXZAgMBAAECggEACJK430UgX9or/vFCICOawPMk3PfXWbAXSthJODa+D/OR\n0CF+AnN4QqJm1NI1qgT+EFT0BxCHC1avkBHPCIFxXJHPY5Rg8hbxRhGoT1P5ONR6\nsV2asIi8EtAmp3qRmdz8Wyb19BmyoDlUHyAsrWhHgajtfyMqdu4Tmnj/P7pKl5sM\nKUSjxjrRc6MLuD7WGkbvV2npeUBPASK5dgYT8ThZLyN1B2MOQfKEOyE+0cA1ctzG\nfluKKqwa+/X67zoUAMu9jPE2NRSnGWC2J0mBA0n5PZZlYfyyG12TzivdOqhpYOnY\n4v8DVcxG7Q7u8A7ExB0492Nq75KXKw/oK3dUUtkrDQKBgQDTezG17f/ev16yRqCo\nqsxC3bbM4z9kF4KQuU1gf2f5i6YYoDEZz2OJ7YLfuDpFKNZjSTc/Whe321AGntI8\n4qZsnjrzjQksnLJUafCKvfwqA3H2oovE7p0B+VjHKrDjWSV8Lnl6ujOd2P3oe90V\n3XAWIvr+qB9bMQ+rUXnPPZK3DQKBgQDAW+3jYmjN08+OBf1z4a0FWIr9fwd81NxY\n0eALYMXz8Z7MTasrkh0Iko+MZaTH0yEECkSrLtU+2N6oyL0Hecq8ZdYSC+dWmvqW\nBr+XYAxlPzZMFWTugfwUbtUIJHznbVVhBnQ+oDrxuCa8W/kIp+t4W3c//yAGpKby\nOFRgIhZm/QKBgAazx86JPWu0yu6BeIP/7btMxYdWyGKGsDef98jQIN5yw4/SO9wi\ni3gKk/Q9JXOdqLW600pps4i7JZ0gGW+ei0Gz/hBL7vd/+9LbDKmI/d3jABCd9CoI\nmec/HMYrHzIFWD/IRUdTcWFWSC2/BzGzM+Mvtp6te1jrhCCc02xy+hxdAoGASyyi\nD1cKNkYsuwhEQOFVSN2Nk/vs5TAa3OtIb6nmMquer6E639A+YHdGekvO1fkA0h9h\nLrUiyWjfu36XwTArtuzleDAGvKXcgH0qqvHyZi8J/TnvM/bAmQunXYNE/PyRfVWU\nYFUmNAkPulUHQga900+LjwsZbP8z7z1sXBV2Q9ECgYBzIdjRwbb4L0OYVAFeVd+M\nkvpVifoW6wsu9GKdQePAoJfoyhaROmKaMPwiNOOTZSmZ8JV+r03yPMVvHPtBpTv6\ntfRROvMV48+Ga8UUVEiPIH2iv0JifvpYEONhP5iashExV2E0QFyW5uAijmi6MGpt\nJUnIrdFWsxWajZrjqxQNzg==\n-----END PRIVATE KEY-----\n"
CLIENT_EMAIL="proteng@cucpbioinfo.iam.gserviceaccount.com"
CLIENT_ID="114275650348444629249"
TOKEN_URI="https://oauth2.googleapis.com/token"
RABBITMQ_URL="amqp://guest:guest@rabbitmq:5672/"
```

### run rabbitmq docker

```sh
docker run --name rabbitmq-for-test -d -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```
### run microservice with python

```sh
cd projects/<project-name>
python3 <entrypoint>.py
```

e.g.

```sh
cd projects/blast
python3 microservice.py
```

## How to add new microservice
- You can add new microservice in the `projects` directory with the structure stated [above](#project-structure)
- You can add more library/common services that will be used in multiple microservice in `pkg` directory
- As the project structure explained above, in the context of each project, to import modules from the `pkg` folder, you will need to have `sys.path.append('../../')` in the entrypoint files.

## How to use microservice in production
As stated at the start of this README, the purpose of this repository is to develop the microservice and put it into a `docker image` for our ML pipeline to use. (info on how to use docker image into a ML pipeline is in [_devops_ _repository_](https://github.com/ProtEngPlus/manual-guides-2023/tree/main/devops))

- The context for each docker file will be at the root of the project !! So that we can also build with the code in pkg folder.

### build docker image
```
docker build -t blast-service -f ./projects/blast/docker/microservice.Dockerfile .
```

### build docker image and publish it to docker repository
- go to `Actions` in github
- select `Build and Publish ML pipeline microservices` on the list of actions
- go to `run workflow` and select whatever `microservice` you want to build
  - select `auto deploy to devops-k8s` to automatically deploy ML pipeline when the image have been builded

PS. you can learn more about github workflow if you have new microservice. (very convenient when deploy microservice to production environment)

### run docker in local to test if your docker image is working
- change port to the specific port in dockerfile
```
docker run -d --name blast-service -p 8080:8080 --env-file=".env" blast-service
```
