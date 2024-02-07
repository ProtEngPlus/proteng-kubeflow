# proteng-kubeflow

This project contains the source code for the ml-pipeline of proteng. 

## For Developers

As the project structure explained below, in the context of each project, to import modules from the `pkg` folder, you will need to have `sys.path.append('../../')` in the entrypoint files.


## Project structure

This is a mono-repo project. Each projects in the `projects` folder are isolated from each other. When running development of a project, the context will be inside each project, i.e. `cd projects/blast` first before starting the app. The `pkg` folder contains the file that is shared across projects. 

<pre>
.
├── pkg                                 # shared
│   ├── common
│   |   ├── rabbitmq.py 
│   |   └── requirements.txt            # each pkg module will have their dependencies declared
|   └── some-library
|       ├── some_module.py
│       └── requirements.txt
| 
└── projects
    |
    └── blast
        ├── docker                      # each projects can have multiple <b>Dockerfile</b>s for different type of apps to build
        |   └── microservice.Dockerfile  
        ├── microservice.py             # the <b>entrypoint</b> files to run
        ├── kubeflow_component.py       # projects can have multiple entrypoints, with each one defines 1 app.
        ├── requirements.txt            # <b>dependencies</b> for 'example' microservice (future should use poetry)
        └── src                         # src for 'example' microservice
            ├── service                 # main source code folder for that project ( contain all logics in service )
            │   └── train.py           
            └── data                  
                └── example_data.txt          
</pre>

## Running in local

create `.env` file and copy the values from notion

```sh
cd projects/<project-name>
python3 <entrypoint>.py
```

e.g.

```sh
cd projects/blast
python3 microservice.py
```

## Docker

The context for each docker file will be at the root of the project !! So that we can also build with the code in pkg folder.

### build docker image
```
docker build -t blast-service -f ./projects/blast/docker/microservice.Dockerfile .
```
### run docker in local
- change port to the specific port in dockerfile
```
docker run -d --name blast-service -p 8080:8080 --env-file=".env" blast-service
```
