# Introduction

### Used Technologies:
- ArgoCD
- Kubernetes
- Github/ Github Actions
- Google Cloud
- Dockerhub
- Docker

### Responsibilities
- Setup of staging and production environment in GKE (@Phillipe Sanio)
- Setup of CI Pipeline (linting, testing) and using (pre-)release capabilities of Github to alter the configuration repositories (@Daniel Lettner)
- Setup of ArgoCD environments in the the staging and production environment to automatically deploy the new (pre-)release versions (@Jakob Pühringer)

### Milestones:
- CI Pipeline
- Kubernetes Environments are setup in Google Cloud
- Automatical deployment via ArgoCD is deployed in the environments
- Presentation of results incl. live demo

### Description of desired state

The goal is to implement a CI/CD Pipeline for the e-arts project. Changes to the main branch or adding a tag should result in tirggering the CI Pipeline. The pipeline consists of linting the project via flake8 and black. Parallel to linting the process for testing the project is executed. If the pipeline is triggered by adding a release tag, the pipeline furthermore builds a new docker images and pushes it onto dockerhub. If release is tagged as prerelease the new Image version is written to the staging environment, otherwise the image is written to the production environment. There are 2 Kubernetes Cluster available: one for production and one for staging. Both environments have ArgoCD installed which is pointing to either the staging or production git repository. Releasing a new version of the "software", results in updating the environments.
 
The pipeline is building in the following way:
1. push onto the main branch / creating a new tag
2. linting the proect. 
3. testing the project via pytest 
4. building a docker image and pushing it to Dockerhub --> after completion, automatic changes in the infrastructure repo
5. ArgoCD detects changes in the config-repo and syncs the new desired state
6. release of the new version in Kubernetes

#### GitOps Workflow 

![GitOpsWorkflow](/ressources/GitOpsWorkflow.png)

# Implementation

## Github Workflow (@Daniel Lettner)

<img width="920" alt="image" src="https://user-images.githubusercontent.com/48688085/212771191-f20ca274-fdbb-4801-8ed5-aea725737d12.png">

The heart of the CI pipeline is the Github Workflow. On every push or pull request the code gets automatically tested and linted in parallel. The linting process is done via _Black_ and _Flake8_ and the testing is done via _pytest_. In case of an error the actor (user who triggered the workflow) will be notified via e-mail. Furthermore we leverage github releases to automatically deploy the new state of the application via docker and use repository dispatches to change the image version in the respective configuration repositories.

### 1. Create repositories

   * create a code repository ```e-arts```
   * create 2 configuration repositories ```e-arts-prod``` and ```e-arts-staging```

### 2. Setup of code repository ```e-arts```

#### Create file ```main.py```

```python
from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    return "Hello Release! Updated by Jakob."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
```

#### Create ```requirement.txt```

```txt
click==8.1.3
Flask==2.2.2
importlib-metadata==6.0.0
itsdangerous==2.1.2
Jinja2==3.1.2
MarkupSafe==2.1.1
Werkzeug==2.2.2
zipp==3.11.0
```

#### Create dummy testing file under ```test/test.py```

```python
def plus(x: int, y: int) -> int:
    return x + y

def test_plus():
    assert plus(2, 1) == 3
```

#### Create Dockerfile

```Dockerfile
FROM python:3.8-alpine

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY main.py /app

ENTRYPOINT [ "python" ]

CMD ["main.py" ]
```

#### Create secrets
Secrets can be created under Settings --> Security --> Actions --> New repository secret. The following secrets need to be added for the workflow to work as intended.

   * DOCKERHUB_USERNAME (```Dockerhub username ```)
   * DOCKERHUB_TOKEN (```Dockerhub password```)
   * PAT (```Personal access token```, how to can be read under [Create personal access token](https://docs.github.com/de/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token))

#### Create Github workflow

<details>
  <summary>Toggle full workflow.yaml</summary>

```yaml
name: CI
on:
  push:
    branches:
        - "**"
  pull_request:
    branches:  
        - "**"
  release:
    types: [published]
  workflow_dispatch:

jobs:

  lint_code:
    name: Code linting
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v3
        
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.8
      
      - name: Install requirement txt
        run: pip install -r requirements.txt
          
      - name: Install Linting frameworks
        run: pip install black flake8
      
      - name: Run flake8
        run: flake8 .
        
      - name: Run black
        run: black .
      
  test_code:
    name: Code testing
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3
        
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.8
      
      - name: Install requirement txt
        run: pip install -r requirements.txt
  
      - name: Install Testing frameworks
        run: pip install pytest
        
      - name: Run Tests
        run: pytest test/test.py
    
  build_and_push:
    if: github.event_name == 'release'
    name: Containerize and Release
    runs-on: ubuntu-latest
    needs: [lint_code, test_code]
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3
        
      - name: Docker meta
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: daniellettner/e-arts
      
      - name: Login to DockerHub
        uses: docker/login-action@v1 
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      
      - name: Build and push
        uses: docker/build-push-action@v2
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          
      - name: get release tag
        id: vars
        run: echo "tag=${GITHUB_REF#refs/*/}" >> $GITHUB_OUTPUT
        
      - name: Repository Dispatch - Staging
        # always update the staging environment
        uses: peter-evans/repository-dispatch@v1
        with:
          token: ${{ secrets.PAT }}
          repository: e-arts/e-arts-config-staging
          event-type: new-image
          client-payload: '{"image": "daniellettner/e-arts:${{ steps.vars.outputs.tag }}"}'
      
      - name: Repository Dispatch - Production
        if: github.event.release.prerelease == false
        uses: peter-evans/repository-dispatch@v1
        with:
          token: ${{ secrets.PAT }}
          repository: e-arts/e-arts-config-prod
          event-type: new-image
          client-payload: '{"image": "daniellettner/e-arts:${{ steps.vars.outputs.tag }}"}'
```



</details>

<details>
  <summary>Toggle explanation of workflow.yaml</summary>

### workflow triggers

```yaml
on:
  push:
    branches:
        - "**"
  pull_request:
    branches:  
        - "**"
  release:
    types: [published]
  workflow_dispatch:
```
The workflow should be triggerable via ```push``` or ```pull request``` from any branch. This will be the backbone of the CI pipeline. Furthermore the workflow also listens to the ```github release event```.

#### lint code job

```yaml
 lint_code:
    name: Code linting
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v3
        
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.8
      
      - name: Install requirement txt
        run: pip install -r requirements.txt
          
      - name: Install Linting frameworks
        run: pip install black flake8
      
      - name: Run flake8
        run: flake8 .
        
      - name: Run black
        run: black .
```

The lint code job is responsible for linting the project and identifying code smells and breaks of conventions. _Black_ and _Flake8_ are used as packages for execution of the linting. 
Detailed explanation:
1. The process is running on ubuntu-latest
2. The process checks out the current repository
3. The process installed the dependencies (Python, packages listed in requirement.txt and the linting packages _Black_ and _Flake8_)
4. The process executes flake8 and black on the root folder

#### test code job

```yaml
test_code:
    name: Code testing
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3
        
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.8
      
      - name: Install requirement txt
        run: pip install -r requirements.txt
  
      - name: Install Testing frameworks
        run: pip install pytest
        
      - name: Run Tests
        run: pytest test/test.py
```
The test code job is responsible for executing the unit tests of the project. _pytest_ is used as packages for execution of the tests. 
Detailed explanation:
1. The process is running on ubuntu-latest
2. The process checks out the current repository
3. The process installed the dependencies (Python, packages listed in requirement.txt and the pytest package)
4. The process executes pytest on the root folder


#### build and push image job

```yaml
 build_and_push:
    name: Containerize and Release
    runs-on: ubuntu-latest
    needs: [lint_code, test_code]
    if: github.event_name == 'release'
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3
        
      - name: Docker meta
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: daniellettner/e-arts
      
      # Login to DockerHub account
      - name: Login to DockerHub
        uses: docker/login-action@v1 
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      
      # Build a Docker image based on provided Dockerfile
      - name: Build and push
        uses: docker/build-push-action@v2
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          
      - name: get release tag
        id: vars
        run: echo "tag=${GITHUB_REF#refs/*/}" >> $GITHUB_OUTPUT
        
      - name: Repository Dispatch - Staging
        # always update the staging environment
        uses: peter-evans/repository-dispatch@v1
        with:
          token: ${{ secrets.PAT }}
          repository: e-arts/e-arts-config-staging
          event-type: new-image
          client-payload: '{"image": "daniellettner/e-arts:${{ steps.vars.outputs.tag }}"}'
      
      - name: Repository Dispatch - Production
        if: github.event.release.prerelease == false
        uses: peter-evans/repository-dispatch@v1
        with:
          token: ${{ secrets.PAT }}
          repository: e-arts/e-arts-config-prod
          event-type: new-image
          client-payload: '{"image": "daniellettner/e-arts:${{ steps.vars.outputs.tag }}"}'
```

The build and push image job is responsible for containerising the code and pushing it into the docker hub registry. Since it is only triggered via a release, it uses the given tag for the release for tagging the newly created image. Which results in more customisable release and tagging behaviour. Furthermore it leverages the github release and pre-release events. Triggering the pipeline via a pre-release only sends a github repository-dispatch event to the ```e-arts-staging``` repository, whereas a trigger from the github release event also sends a repository-dispatch to the pro ```e-arts-prod``` repository.


Detailed explanation:
1. The process is running on ubuntu-latest
2. The process runs only after the successful completion of the ```lint_code``` and ```test_code``` job
3. The process runs only if the triggering event is a release event. This prevents the job to be executed from a normal ```push``` or ```pull_request``` event
4. The process checks out the current repository
5. The process uses the ```docker/metadata-action@v4``` action to extract the tags from the release. This will create the name for the newly created image including the image name and the tag for versioning. 
6. The process uses ```docker/login-action@v1``` to login into the docker hub account. It uses the secret which were created above.
7. The process builds and pushes the image onto docker hub
8. The process uses the github action ```peter-evans/repository-dispatch@v1``` to execute the repository dispatch to the ```e-arts-staging``` and ```e-arts-prod repository```

</details>

### 3. Setup of configuration repositories ```e-arts-prod``` and ```e-arts-staging```

Generally speaking ```e-arts-prod``` and ```e-arts-staging``` are setup exactly the same. The only difference between the 2 repositories is the ```repoURL```in the ```application.yaml``` file. 


#### Create ```application.yaml```

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: e-arts-app-argo-application
  namespace: argocd
spec:
  project: default

  source:
    repoURL: https://github.com/e-arts/e-arts-config-staging.git
    # repoURL: https://github.com/e-arts/e-arts-config-prod.git
    targetRevision: HEAD
    path: dev
  destination: 
    server: https://kubernetes.default.svc
    namespace: e-arts-app

  syncPolicy:
    syncOptions:
    - CreateNamespace=true

    automated:
      selfHeal: true
      prune: true
```

* The repoURL defines the observed repository
* The path defines the folder in the observed repository witch should be synced.
* Pruning the application means that if Argo CD detects that the resource is no longer defined in Git. It will be automatically deleted in the Kubernetes Cluster.
* Self heal means that if Argo CD detects that resources differ from the state declared in Git, it will automatically sync the resource and replace it with the state defined in Git. This prevents manual changes to resources and only allows the state of Git.

#### Create ```deployment.yaml``` under ```/dev``` folder
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: e-arts-app
spec:
  selector:
    matchLabels:
      app: e-arts-app
  replicas: 3
  template:
    metadata:
      labels:
        app: e-arts-app
    spec:
      containers:
        - name: e-arts-app
          image: "[user]/e-arts:v0.0.1"
          ports:
            - containerPort: 3000
```

Defines the Deployment. It references the image of the container to be deployed and states the port which should be opened for the container. Furthermore it states that the deployment should have 3 replicas.


#### Create ```service.yaml``` under ```/dev``` folder

```yaml
apiVersion: v1
kind: Service
metadata:
  name: e-arts-app-service
spec:
  selector:
    app: e-arts-app
  ports:
  - port: 3000
    protocol: TCP
    targetPort: 3000
```

Defines the service to be deployed. It references the resource defined in ```deployment.yaml``` via the app-selector. Furthermore it defines the port on witch the application should be available.

### 4. Testing and triggering the Github pipeline


<img width="1437" alt="image" src="https://user-images.githubusercontent.com/48688085/212766402-e14ae0bb-6291-4d06-8a35-425cb4ba4257.png">

As defined the ```push``` event should only trigger the ```linting job``` and the ```testing job```, both of which run in parallel. The ```build and push``` job is skipped.

<img width="1437" alt="image" src="https://user-images.githubusercontent.com/48688085/212766702-4fd5ccb0-888a-491f-9172-60a46bc72b4b.png">

Triggering the pipeline via a release event also triggers the ```build and push``` job. This includes pushing the container to docker hub and creating the repository dispatch, which results in updating the config repositories and specifically the ```deployment.yaml```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: e-arts-app
spec:
  selector:
    matchLabels:
      app: e-arts-app
  replicas: 3
  template:
    metadata:
      labels:
        app: e-arts-app
    spec:
      containers:
        - name: e-arts-app
          image: "daniellettner/e-arts:v20.0.1"
          ports:
            - containerPort: 3000
```


## Argo CD
## Deployment via Google Cloud (GKE)







## Setup of ArgoCD Deployment in Kubernetes

Setup can be used by local deployment such as Minikube oder Docker Desktop

1. Install ArgoCD
```
 kubectl create namespace argocd
 kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
 ```

2. Open Port to ArgoCD on local machine
```
 kubectl port-forward svc/argocd-server -n argocd 8080:443
 ```

3. Get username and password: according to documentation username = admin
```
 kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath=”{.data.password}” | base64 -d; echo
```

4. Browse to http://localhost:8080 to access ArgoUI

Configure ArgoCD to track the config repository.

1. Checkout the e-arts-config git repository
2. Apply the application.yaml to setup the tracking and deploy app
```
 kubectl apply -f application.yaml
 ```
3. Test if application is working (Port should match to flask app)
```
 kubectl port-forward svc/e-arts-app-service 3000:3000 -n e-arts-app
 ```
4. Browse to http://localhost:3000 to access the flask app
