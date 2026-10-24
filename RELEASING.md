# Release Management & Versioning Convention

This document outlines the release discipline, semantic versioning strategy, and rollback procedures for this application.

- **GitHub Repository:** [https://github.com/Sievphor/cloud_home_work_3.git](https://github.com/Sievphor/cloud_home_work_3.git)
- **Amazon ECR URI:** `908157891706.dkr.ecr.us-east-1.amazonaws.com/sievphor-homework3`

---

## 1. Versioning Convention: Semantic Versioning (SemVer)

All releases in this repository strictly adhere to [Semantic Versioning 2.0.0](https://semver.org/) formatted as:

$$\mathbf{vMAJOR.MINOR.PATCH}$$

- **MAJOR (v1.0.0 -> v2.0.0):** Incompatible API changes, major architectural redesigns, or breaking structural modifications.
- **MINOR (v1.0.0 -> v1.1.0):** New backwards-compatible functionality, features, or UI improvements added.
- **PATCH (v1.1.0 -> v1.1.1):** Backwards-compatible bug fixes, security patches, or small configuration updates.

### Release Milestones in this Project:
- `v1.0.0`: Initial stable release running on Docker Swarm.
- `v1.1.0`: Feature update adding enhanced metrics and dashboard styles.
- `v1.2.0`: Latest stable release with complete release tracking and health checks.

---

## 2. How to Cut a Release

Follow these steps to create and publish a new versioned release:

### Step 1: Ensure code is clean and tested
Make the necessary changes and commit them to the `main` branch:
```bash
git add .
git commit -m "feat: release version v1.2.0"
git push origin main
```

### Step 2: Create an annotated Git tag
Always create an annotated tag with a meaningful release message:
```bash
git tag -a v1.2.0 -m "Release v1.2.0: production release"
```

### Step 3: Push the tag to GitHub
```bash
git push origin v1.2.0
```

### Step 4: Automated CI/CD Execution
Once the tag is pushed:
1. GitHub webhook sends a tag-push event (`refs/tags/*`) to Jenkins.
2. Jenkins extracts the tag name (`v1.2.0`).
3. Jenkins authenticates with Amazon ECR and builds the Docker image tagged exactly with `908157891706.dkr.ecr.us-east-1.amazonaws.com/sievphor-homework3:v1.2.0`.
4. Jenkins pushes the image to Amazon ECR. The tag is immutable and will never be overwritten.
5. Jenkins connects to the Docker Swarm Manager on AWS EC2 (`13.220.98.249`) and triggers a rolling update (`docker service update --image ...`).

---

## 3. How to Perform a Safe, Zero-Downtime Rollback

If a release introduces a regression or defect, an operator can immediately roll back to a known good version without rebuilding anything:

### Step 1: Open Jenkins Dashboard
1. Navigate to the Jenkins pipeline job `sievphor-homework3`.
2. Click **Build with Parameters**.

### Step 2: Configure Rollback Parameters
- **ACTION:** Select `rollback`
- **VERSION:** Enter the target prior tag (e.g., `v1.0.0`)

### Step 3: Automated Rollback Execution
When the rollback build runs:
1. **ECR Verification:** Jenkins queries Amazon ECR (`aws ecr describe-images`) to ensure that the pre-existing image for `v1.0.0` is present.
2. **No Rebuild:** Jenkins does NOT build a new image, avoiding any code compilation risks.
3. **Swarm Rolling Update:** Jenkins instructs Docker Swarm on EC2 to update the service image to `908157891706.dkr.ecr.us-east-1.amazonaws.com/sievphor-homework3:v1.0.0`.
4. **Zero Downtime:** Docker Swarm updates containers one replica at a time (`parallelism: 1`, `delay: 10s`), ensuring the service remains accessible throughout the rollback.
