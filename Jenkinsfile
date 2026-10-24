pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        skipDefaultCheckout(false)
        buildDiscarder(
            logRotator(
                numToKeepStr: '25',
                artifactNumToKeepStr: '10'
            )
        )
    }

    parameters {
        choice(
            name: 'ACTION',
            choices: [
                'all',
                'build',
                'push',
                'deploy',
                'rollback'
            ],
            description: 'Select action to execute. "all" builds, pushes, and deploys sequentially.'
        )

        string(
            name: 'VERSION',
            defaultValue: 'v1.0.0',
            description: 'Target Semantic Version / Git Tag (e.g. v1.0.0, v1.1.0, v1.2.0).'
        )
    }

    environment {
        // AWS & ECR Configuration
        AWS_REGION      = 'us-east-1'
        AWS_ACCOUNT_ID  = '908157891706'
        ECR_REPO        = 'sievphor-homework3'

        ECR_REGISTRY    = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        ECR_IMAGE       = "${ECR_REGISTRY}/${ECR_REPO}"

        // Swarm Manager EC2 Configuration
        MANAGER_HOST    = '3.91.30.20'
        MANAGER_USER    = 'ubuntu'
        STACK_NAME      = 'homework3'
        SERVICE_NAME    = 'homework3_web'

        // Jenkins Credentials IDs
        SSH_CREDENTIALS = 'ec2-server-key'
        AWS_CREDENTIALS = 'aws-credentials'

        PATH = '/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin'
    }

    stages {
        stage('Validate Parameters & Version') {
            steps {
                script {
                    def action = params.ACTION?.trim() ?: 'all'
                    def version = params.VERSION?.trim()

                    // If triggered automatically by Git Tag push webhook
                    if ((!version || version == '') && env.TAG_NAME) {
                        version = env.TAG_NAME
                    } else if ((!version || version == '') && env.GIT_TAG_NAME) {
                        version = env.GIT_TAG_NAME
                    }

                    if (!version) {
                        error('VERSION parameter is required. Example: v1.0.0, v1.1.0, v1.2.0')
                    }

                    if (!(version ==~ /^v?[0-9]+\.[0-9]+\.[0-9]+.*$/)) {
                        echo "WARNING: Version '${version}' does not strictly follow Semantic Versioning (vMAJOR.MINOR.PATCH)."
                    }

                    env.IMAGE_TAG = version
                    env.FULL_IMAGE_NAME = "${env.ECR_IMAGE}:${version}"

                    echo '======================================'
                    echo "PIPELINE ACTION : ${action}"
                    echo "TARGET VERSION  : ${env.IMAGE_TAG}"
                    echo "FULL ECR IMAGE  : ${env.FULL_IMAGE_NAME}"
                    echo '======================================'
                }
            }
        }

        stage('Checkout Version') {
            when {
                expression {
                    params.ACTION in ['all', 'build', 'push']
                }
            }
            steps {
                echo "Checking out source code for version ${env.IMAGE_TAG}..."
                checkout scm
            }
        }

        stage('Build Docker Image') {
            when {
                expression {
                    params.ACTION in ['all', 'build']
                }
            }
            steps {
                echo "======================================"
                echo "Building Docker image: ${env.FULL_IMAGE_NAME}"
                echo "======================================"
                sh '''
                    set -e
                    docker build \
                        -t "${FULL_IMAGE_NAME}" \
                        -t "${ECR_REPO}:${IMAGE_TAG}" \
                        .

                    docker image inspect "${FULL_IMAGE_NAME}" \
                        --format 'Built Image ID: {{.Id}} | Created: {{.Created}}'
                '''
            }
        }

        stage('Push to AWS ECR') {
            when {
                expression {
                    params.ACTION in ['all', 'push']
                }
            }
            steps {
                echo "======================================"
                echo "Pushing immutable image to Amazon ECR"
                echo "======================================"
                sh '''
                    set -e

                    # Authenticate Docker client with ECR
                    aws ecr get-login-password --region "${AWS_REGION}" | \
                    docker login --username AWS --password-stdin "${ECR_REGISTRY}"

                    # Push the versioned tag to ECR
                    docker push "${FULL_IMAGE_NAME}" || true

                    # Verify image existence in ECR
                    aws ecr describe-images \
                        --region "${AWS_REGION}" \
                        --repository-name "${ECR_REPO}" \
                        --image-ids imageTag="${IMAGE_TAG}" \
                        --query 'imageDetails[0].[imageTags,imageDigest,imagePushedAt]' \
                        --output table

                    echo "Successfully pushed immutable image: ${FULL_IMAGE_NAME}"
                '''
            }
        }

        stage('Deploy to Docker Swarm') {
            when {
                expression {
                    params.ACTION in ['all', 'deploy']
                }
            }
            steps {
                echo "======================================"
                echo "Deploying ${FULL_IMAGE_NAME} to Docker Swarm"
                echo "======================================"
                withCredentials([
                    sshUserPrivateKey(
                        credentialsId: "${SSH_CREDENTIALS}",
                        keyFileVariable: 'SSH_KEY',
                        usernameVariable: 'SSH_USER'
                    )
                ]) {
                    sh '''
                        set -e
                        KEY_OPT="-i $SSH_KEY"
                        if [ -f "/var/jenkins_home/.ssh/id_rsa" ]; then
                            KEY_OPT="-i /var/jenkins_home/.ssh/id_rsa"
                        fi

                        TOKEN_FILE="$WORKSPACE/ecr-deploy-token.txt"
                        aws ecr get-login-password --region "${AWS_REGION}" > "$TOKEN_FILE"
                        chmod 600 "$TOKEN_FILE"

                        scp $KEY_OPT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
                            "$TOKEN_FILE" "${MANAGER_USER}@${MANAGER_HOST}:/tmp/ecr-deploy-token.txt"

                        ssh $KEY_OPT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
                            "${MANAGER_USER}@${MANAGER_HOST}" \
                            "
                                set -e
                                cat /tmp/ecr-deploy-token.txt | \
                                sudo docker login --username AWS --password-stdin '${ECR_REGISTRY}'
                                rm -f /tmp/ecr-deploy-token.txt

                                if ! sudo docker service inspect '${SERVICE_NAME}' >/dev/null 2>&1; then
                                    echo 'Service not found. Initializing stack deployment...'
                                    sudo docker service create --name ${SERVICE_NAME} --replicas 3 -p 80:80 --with-registry-auth '${FULL_IMAGE_NAME}'
                                else
                                    echo 'Updating existing service ${SERVICE_NAME} to ${FULL_IMAGE_NAME}...'
                                    sudo docker service update \
                                        --with-registry-auth \
                                        --image '${FULL_IMAGE_NAME}' \
                                        --update-parallelism 1 \
                                        --update-delay 10s \
                                        --update-order start-first \
                                        --update-failure-action rollback \
                                        '${SERVICE_NAME}'
                                fi

                                echo 'Deployment updated successfully.'
                            "
                    '''
                }
            }
        }

        stage('Rollback Docker Swarm (No Rebuild)') {
            when {
                expression {
                    params.ACTION == 'rollback'
                }
            }
            steps {
                echo "=========================================================="
                echo "EXECUTING ROLLBACK TO EXISTING IMAGE: ${env.FULL_IMAGE_NAME}"
                echo "No source code rebuild or new image creation performed."
                echo "=========================================================="
                withCredentials([
                    sshUserPrivateKey(
                        credentialsId: "${SSH_CREDENTIALS}",
                        keyFileVariable: 'SSH_KEY',
                        usernameVariable: 'SSH_USER'
                    )
                ]) {
                    sh '''
                        set -e
                        KEY_OPT="-i $SSH_KEY"
                        if [ -f "/var/jenkins_home/.ssh/id_rsa" ]; then
                            KEY_OPT="-i /var/jenkins_home/.ssh/id_rsa"
                        fi

                        echo "Step 1: Confirming rollback image exists in Amazon ECR..."
                        aws ecr describe-images \
                            --region "${AWS_REGION}" \
                            --repository-name "${ECR_REPO}" \
                            --image-ids imageTag="${IMAGE_TAG}" \
                            --query 'imageDetails[0].[imageTags,imageDigest,imagePushedAt]' \
                            --output table

                        echo "[ROLLBACK] Deploying pre-built immutable image directly from ECR (No Rebuild)"

                        TOKEN_FILE="${WORKSPACE}/ecr-rollback-token.txt"
                        REMOTE_TOKEN="/tmp/ecr-rollback-token.txt"

                        aws ecr get-login-password --region "${AWS_REGION}" > "${TOKEN_FILE}"
                        chmod 600 "${TOKEN_FILE}"

                        scp $KEY_OPT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
                            "${TOKEN_FILE}" "${MANAGER_USER}@${MANAGER_HOST}:${REMOTE_TOKEN}"

                        echo "Step 2: Redeploying prior image on Docker Swarm via Rolling Update..."
                        ssh $KEY_OPT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
                            "${MANAGER_USER}@${MANAGER_HOST}" \
                            "
                                set -e
                                cat '${REMOTE_TOKEN}' | sudo docker login --username AWS --password-stdin '${ECR_REGISTRY}'
                                rm -f '${REMOTE_TOKEN}'

                                echo 'Current active image on service:'
                                sudo docker service inspect --format '{{.Spec.TaskTemplate.ContainerSpec.Image}}' '${SERVICE_NAME}'

                                echo 'Triggering rolling rollback to ${FULL_IMAGE_NAME}...'
                                sudo docker service update \
                                    --with-registry-auth \
                                    --image '${FULL_IMAGE_NAME}' \
                                    --update-parallelism 1 \
                                    --update-delay 10s \
                                    --update-order stop-first \
                                    --update-failure-action rollback \
                                    '${SERVICE_NAME}'

                                echo '--- Rollback Verified ---'
                                sudo docker service inspect --format 'Active Image: {{.Spec.TaskTemplate.ContainerSpec.Image}}' '${SERVICE_NAME}'
                            "
                    '''
                }
            }
        }

        stage('Verify Running Service & Tasks') {
            when {
                anyOf {
                    expression { params.ACTION in ['all', 'deploy', 'rollback'] }
                }
            }
            steps {
                withCredentials([
                    sshUserPrivateKey(
                        credentialsId: "${SSH_CREDENTIALS}",
                        keyFileVariable: 'SSH_KEY',
                        usernameVariable: 'SSH_USER'
                    )
                ]) {
                    sh '''
                        set -e
                        KEY_OPT="-i $SSH_KEY"
                        if [ -f "/var/jenkins_home/.ssh/id_rsa" ]; then
                            KEY_OPT="-i /var/jenkins_home/.ssh/id_rsa"
                        fi
                        ssh $KEY_OPT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
                            "${MANAGER_USER}@${MANAGER_HOST}" \
                            "
                                echo '======================================'
                                echo 'Service Status:'
                                sudo docker service ls --filter name='${SERVICE_NAME}'

                                echo '======================================'
                                echo 'Task Replica Placement:'
                                sudo docker service ps '${SERVICE_NAME}'
                                echo '======================================'
                            "
                    '''
                }
            }
        }
    }

    post {
        success {
            echo "=========================================================="
            echo "Pipeline Completed Successfully!"
            echo "Action  : ${params.ACTION}"
            echo "Version : ${env.IMAGE_TAG}"
            echo "Manager : http://${MANAGER_HOST}:80"
            echo "Worker 1: http://34.229.219.41:80"
            echo "Worker 2: http://54.90.208.206:80"
            echo "=========================================================="
        }
        failure {
            echo "=========================================================="
            echo "Pipeline Failed! Review console error output above."
            echo "=========================================================="
        }
        always {
            sh 'rm -f "$WORKSPACE"/ecr*.txt || true'
        }
    }
}
