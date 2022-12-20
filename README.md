# e-arts

## Proposal

The goal is to implement a CI/CD Pipeline for the e-arts project. Changes to the main branch should result in triggering the CI Pipeline. The result of the pipeline is a docker container which gets pushed to the docker hub registry. Furthermore during the build step the Infrastructure repo is automatically changed which triggeres the ArgoCD controller and thus triggers a sync of state. Which results in the application beeing released onto the Kubernetes cluster.
 
The pipeline is building in the following way:
1. push onto the main branch 
2. linting the proect. 
3. testing the project via pytest 
4. building a docker image and pushing it to Dockerhub --> after completion, automatic changes in the infrastructure repo
5. ArgoCD detects changes in the repo and syncs the new desired state
6. release of the new version

## GitOps Workflow (desired state)

![GitOpsWorkflow](/ressources/GitOpsWorkflow.png)
