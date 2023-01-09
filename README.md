# e-arts 

## Proposal

Used Components:
- ArgoCD
- Kubernetes
- Github/ Github Actions
- Google Cloud

The goal is to implement a CI/CD Pipeline for the e-arts project. Changes to the main branch or adding a tag should result in tirggering the CI Pipeline. The pipeline consists of linting the project via flake8 and black. Parallel to linting the project a step for testing the project is executed. If the pipeline is triggered by adding a release tag the pipeline furthermore builds a new docker images and pushes it onto dockerhub. If release is tagged as prerelease the new Image version is written to the staging environment, otherwise the image is written to the production environment. There are 2 Kubernetes Cluster availabel: one for production and one for staging. Both have ArgoCD installed which is pointing to either the staging or production git repository. Release a new version of the "software" results in updating the environments.
 
The pipeline is building in the following way:
1. push onto the main branch / creating a new tag
2. linting the proect. 
3. testing the project via pytest 
4. building a docker image and pushing it to Dockerhub --> after completion, automatic changes in the infrastructure repo
5. ArgoCD detects changes in the repo and syncs the new desired state
6. release of the new version in Kubernetes

## GitOps Workflow (desired state)

![GitOpsWorkflow](/ressources/GitOpsWorkflow.png)

## Sources
* https://igboie.medium.com/kubernetes-ci-cd-with-github-github-actions-and-argo-cd-36b88b6bda64


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
 kubectl port-forward svc/node-app-service 3000:3000 -n node-app
 ```
4. Browse to http://localhost:3000 to access the flask app
