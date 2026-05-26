# Jenkins Server Pipeline Deployment

This project is designed to run in Jenkins after each Git commit.

## Server prerequisites

Install these on the Jenkins server:

```bash
sudo apt update
sudo apt install -y openjdk-17-jdk git python3 python3-pip python3-venv unzip
pip3 install uv
```

Jenkins plugins:

- Pipeline
- Git
- JUnit
- Allure Jenkins Plugin
- Credentials Binding

## Jenkins job

Create a Pipeline job named:

```text
logistics-api-test
```

Use:

```text
Pipeline script from SCM
```

Set:

```text
SCM: Git
Repository URL: your repository URL
Branch: main or master
Script Path: Jenkinsfile
```

## Trigger after code submit

For a public or reachable Jenkins server, use Git webhook.

For a simple server deployment, the `Jenkinsfile` already includes:

```groovy
triggers {
    pollSCM('H/2 * * * *')
}
```

Jenkins checks the Git repository about every 2 minutes. If a new commit is found, it pulls the code and runs the pipeline.

## Pipeline flow

The `Jenkinsfile` does the following:

1. Pulls the latest code with `checkout scm`.
2. Installs dependencies with `uv sync`.
3. Starts the Flask Mock Server with `mock_server/api_server/start_mock.py`.
4. Runs automation tests with `uv run python run.py run`.
5. Archives `report/results.xml` as JUnit results.
6. Archives `report/temp` as Allure results.
7. Archives `logs/**` and `report/**`.

## Required ports

Open these ports in the cloud security group if you need browser access:

```text
22    SSH
8080  Jenkins
9000  Test platform frontend
```

The Mock Server can stay local to the Jenkins server:

```text
127.0.0.1:8787
```

No public access is required for the Mock Server if Jenkins and Mock run on the same server.
