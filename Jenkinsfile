pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
    }

    triggers {
        pollSCM('H/2 * * * *')
    }

    environment {
        PYTHONUTF8 = '1'
        PYTHONIOENCODING = 'utf-8'
        MOCK_HOST = '127.0.0.1'
        MOCK_PORT = '8787'
    }

    stages {
        stage('Checkout') {
            steps {
                retry(3) {
                    checkout scm
                }
            }
        }

        stage('Install') {
            steps {
                script {
                    if (isUnix()) {
                        sh 'uv sync'
                    } else {
                        bat 'uv sync'
                    }
                }
            }
        }

        stage('Start Mock Server') {
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                            mkdir -p logs
                            pkill -f "mock_server/api_server/start_mock.py" || true
                            nohup uv run python mock_server/api_server/start_mock.py > logs/mock_server.log 2>&1 &
                            sleep 5
                        '''
                    } else {
                        bat '''
                            if not exist logs mkdir logs
                            powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*mock_server*start_mock.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }; Start-Process -FilePath 'uv' -ArgumentList @('run','python','mock_server\\\\api_server\\\\start_mock.py') -WorkingDirectory '%CD%' -WindowStyle Hidden -RedirectStandardOutput 'logs\\\\mock_server.log' -RedirectStandardError 'logs\\\\mock_server.err.log'; Start-Sleep -Seconds 5"
                        '''
                    }
                }
            }
        }

        stage('Test') {
            steps {
                script {
                    if (isUnix()) {
                        sh 'uv run python run.py run'
                    } else {
                        bat 'uv run python run.py run'
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                if (fileExists('report/results.xml')) {
                    junit allowEmptyResults: true, testResults: 'report/results.xml'
                }
                if (fileExists('report/temp')) {
                    try {
                        allure includeProperties: false, jdk: '', results: [[path: 'report/temp']]
                    } catch (err) {
                        echo "Allure publish skipped: ${err}"
                    }
                }
                archiveArtifacts allowEmptyArchive: true, artifacts: 'logs/**, report/**'
            }
        }
    }
}
