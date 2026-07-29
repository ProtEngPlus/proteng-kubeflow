# proteng-kubeflow

This repository is basically a place that create _**microservices docker image**_ for ML pipeline

PS. at first **_we_**(the first proteng students group to do this project) plan to use kubeflow for our pipeline (hence the name "kubeflow"). But later on into the project, we decided not to use it(kubeflow) and you can find more info on [_devops_ _repository_](https://github.com/ProtEngPlus/manual-guides-2023/tree/main/devops)

See [SETUP.md](./SETUP.md) to run a microservice locally, and [CONTRIBUTING.md](./CONTRIBUTING.md) for commit conventions and pre-commit hooks.

## Table of Contents
- [Project Structure](#project-structure)
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
