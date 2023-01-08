# e-arts (https://igboie.medium.com/kubernetes-ci-cd-with-github-github-actions-and-argo-cd-36b88b6bda64)

## Proposal

The goal is to implement a CI/CD Pipeline for the e-arts project. Changes to the main branch or adding a tag should result in tirggering the CI Pipeline. The pipeline consists of linting the project via flake8 and black. Parallel to linting the project a step for testing the project is executed. If the pipeline is triggered by adding a release tag the pipeline furthermore builds a new docker images and pushes it onto dockerhub. The tag from the release is added as the tag for the docker image. Furthermore the version specified in the manifest of the infrastructure repo is altered which results in ArgoCD automatically triggering a new release in the Kubernetes Cluster. Which results in the application beeing released onto the Kubernetes cluster.
 
The pipeline is building in the following way:
1. push onto the main branch / creating a new tag
2. linting the proect. 
3. testing the project via pytest 
4. building a docker image and pushing it to Dockerhub --> after completion, automatic changes in the infrastructure repo
5. ArgoCD detects changes in the repo and syncs the new desired state
6. release of the new version in Kubernetes

## GitOps Workflow (desired state)

![GitOpsWorkflow](/ressources/GitOpsWorkflow.png)
