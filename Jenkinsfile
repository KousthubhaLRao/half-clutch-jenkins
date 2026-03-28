pipeline {
    agent any

    stages {
        stage('Fetch Code') {
            steps {
                echo 'Pulling from GitHub...'
            }
        }
        stage('Security Scan') {
            steps {
                echo 'Running Snyk scan...'
            }
        }
        stage('Docker Build') {
            steps {
                echo 'Building image...'
            }
        }
        stage('Push to Registry') {
            steps {
                echo 'Pushing to Docker Hub...'
            }
        }
        stage('be happy')
        {
            steps
            {
                echo 'ohohoho'
            }
        }
    }
}