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
        MANAGER_HOST    = '13.220.98.249'
        MANAGER_USER    = 'ubuntu'
        STACK_NAME      = 'homework3'
        SERVICE_NAME    = 'homework3_web'

        // Jenkins Credentials IDs
        AWS_CREDENTIALS = 'aws-credentials'
        SSH_CREDENTIALS = 'swarm-ssh-key'

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
                    set -eu
                    docker buildx build \
                        --platform linux/amd64 \
                        --pull \
                        --tag "${FULL_IMAGE_NAME}" \
                        --load \
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
                withCredentials([
                    [
                        $class: 'AmazonWebServicesCredentialsBinding',
                        credentialsId: "${AWS_CREDENTIALS}"
                    ]
                ]) {
                    sh '''
                        set -eu

                        # Authenticate Docker client with ECR
                        aws ecr get-login-password --region "${AWS_REGION}" | \
                        docker login --username AWS --password-stdin "${ECR_REGISTRY}"

                        # Push the versioned tag to ECR
                        docker push "${FULL_IMAGE_NAME}"

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
                    [
                        $class: 'AmazonWebServicesCredentialsBinding',
                        credentialsId: "${AWS_CREDENTIALS}"
                    ]
                ]) {
                    sshagent(["${SSH_CREDENTIALS}"]) {
                        sh '''
                            set -eu

                            TOKEN_FILE="$WORKSPACE/ecr-token.txt"
                            aws ecr get-login-password --region "${AWS_REGION}" > "$TOKEN_FILE"
                            chmod 600 "$TOKEN_FILE"

                            # Transfer token to Swarm Manager
                            scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
                                "$TOKEN_FILE" "${MANAGER_USER}@${MANAGER_HOST}:/tmp/ecr-deploy-token.txt"

                            # Execute rolling deployment on Swarm Manager
                            ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
                                "${MANAGER_USER}@${MANAGER_HOST}" \
                                "
                                    set -eu
                                    cat /tmp/ecr-deploy-token.txt | \
                                    docker login --username AWS --password-stdin '${ECR_REGISTRY}'
                                    rm -f /tmp/ecr-deploy-token.txt

                                    # Check if service exists; create via stack or update in place
                                    if ! docker service inspect '${SERVICE_NAME}' >/dev/null 2>&1; then
                                        echo 'Service not found. Initializing stack deployment...'
                                        sed 's|IMAGE_PLACEHOLDER|${FULL_IMAGE_NAME}|g' docker-stack.yml > /tmp/deploy-stack.yml
                                        docker stack deploy --with-registry-auth -c /tmp/deploy-stack.yml '${STACK_NAME}'
                                    else
                                        echo 'Updating existing service ${SERVICE_NAME} to ${FULL_IMAGE_NAME}...'
                                        docker service update \
                                            --with-registry-auth \
                                            --image '${FULL_IMAGE_NAME}' \
                                            --update-parallelism 1 \
                                            --update-delay 10s \
                                            --update-order start-first \
                                            --update-failure-action rollback \
                                            --detach=false \
                                            '${SERVICE_NAME}'
                                    fi

                                    echo 'Deployment updated successfully.'
                                "
                        '''
                    }
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
                    [
                        $class: 'AmazonWebServicesCredentialsBinding',
                        credentialsId: "${AWS_CREDENTIALS}"
                    ]
                ]) {
                    sshagent(["${SSH_CREDENTIALS}"]) {
                        sh '''
                            set -eu

                            echo "Step 1: Confirming rollback image exists in Amazon ECR..."
                            aws ecr describe-images \
                                --region "${AWS_REGION}" \
                                --repository-name "${ECR_REPO}" \
                                --image-ids imageTag="${IMAGE_TAG}" \
                                >/dev/null

                            echo "Confirmed: ${FULL_IMAGE_NAME} is available in ECR."

                            TOKEN_FILE="${WORKSPACE}/ecr-rollback-token.txt"
                            REMOTE_TOKEN="/tmp/ecr-rollback-token.txt"

                            aws ecr get-login-password --region "${AWS_REGION}" > "${TOKEN_FILE}"
                            chmod 600 "${TOKEN_FILE}"

                            scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
                                "${TOKEN_FILE}" "${MANAGER_USER}@${MANAGER_HOST}:${REMOTE_TOKEN}"

                            echo "Step 2: Redeploying prior image on Docker Swarm via Rolling Update..."
                            ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
                                "${MANAGER_USER}@${MANAGER_HOST}" \
                                "
                                    set -eu
                                    cat '${REMOTE_TOKEN}' | docker login --username AWS --password-stdin '${ECR_REGISTRY}'
                                    rm -f '${REMOTE_TOKEN}'

                                    echo 'Current active image on service:'
                                    docker service inspect --format '{{.Spec.TaskTemplate.ContainerSpec.Image}}' '${SERVICE_NAME}'

                                    echo 'Triggering rolling rollback to ${FULL_IMAGE_NAME}...'
                                    docker service update \
                                        --with-registry-auth \
                                        --image '${FULL_IMAGE_NAME}' \
                                        --update-parallelism 1 \
                                        --update-delay 10s \
                                        --update-order stop-first \
                                        --update-failure-action rollback \
                                        --detach=false \
                                        '${SERVICE_NAME}'

                                    echo '--- Rollback Verified ---'
                                    docker service inspect --format 'Active Image: {{.Spec.TaskTemplate.ContainerSpec.Image}}' '${SERVICE_NAME}'
                                "
                        '''
                    }
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
                sshagent(["${SSH_CREDENTIALS}"]) {
                    sh '''
                        set -eu
                        ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
                            "${MANAGER_USER}@${MANAGER_HOST}" \
                            "
                                echo '======================================'
                                echo 'Service Status:'
                                docker service ls --filter name='${SERVICE_NAME}'

                                echo '======================================'
                                echo 'Task Replica Placement:'
                                docker service ps '${SERVICE_NAME}'
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
            cleanWs(
                cleanWhenNotBuilt: false,
                deleteDirs: true,
                disableDeferredWipeout: false,
                notFailBuild: true
            )
        }
    }
}
