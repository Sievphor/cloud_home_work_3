# Homework 3: Release Management with GitHub Tags & Jenkins Build/Push/Deploy/Rollback

**Course:** Advanced Cloud Technology  
**Lecturer:** Mr. Krol Noeurn  
**Student:** TONN Sievphor  
**GitHub Repository:** [https://github.com/Sievphor/cloud_home_work_3.git](https://github.com/Sievphor/cloud_home_work_3.git)  
**Academic Year:** 2026 - 2027  

---

## 1. Project Overview
Homework 3 introduces professional release discipline to the CI/CD pipeline. Instead of deploying on every commit, Jenkins triggers exclusively on Git tag pushes formatted according to Semantic Versioning (`vMAJOR.MINOR.PATCH`). 

Every released Docker image is built with an immutable tag matching the Git tag and pushed to Amazon ECR without overwriting prior tags. Furthermore, an explicit on-demand **Rollback** mechanism allows operators to redeploy any prior verified image directly to the running Docker Swarm cluster with zero rebuild and zero downtime.

---

## 2. Release & Rollback Architecture

```text
                  ┌───────────────────────────────┐
                  │ Developer pushes Git Tag      │
                  │ (e.g., git push origin v1.2.0)│
                  └──────────────┬────────────────┘
                                 │ Webhook (tags only)
                                 ▼
                     ┌───────────────────────┐
                     │ Jenkins Pipeline Job  │
                     │ (ACTION, VERSION)     │
                     └───────────┬───────────┘
                                 │
         ┌───────────────────────┴───────────────────────┐
         │                                               │
   [ACTION = all / build / push]                  [ACTION = rollback]
         │                                               │
         ▼                                               ▼
1. Build Docker image with exact tag       1. Verify image exists in ECR
2. Push immutable image to ECR             2. Pull existing image directly (NO REBUILD)
3. Deploy rolling update to Swarm          3. Redeploy service via Swarm Rolling Update
         │                                               │
         └───────────────────────┬───────────────────────┘
                                 │
                                 ▼
                 Docker Swarm Service on AWS EC2
                 ┌──────────────────────────────────────────────┐
                 │  Swarm Manager:  http://13.220.98.249:80     │
                 │  Swarm Worker 1: http://34.229.219.41:80     │
                 │  Swarm Worker 2: http://54.90.208.206:80     │
                 │  Replicas: 3 (Zero Downtime Rolling Update)  │
                 └──────────────────────────────────────────────┘
```

---

## 3. Versioning Strategy (Semantic Versioning)
Tags strictly follow `vMAJOR.MINOR.PATCH`:
- **v1.0.0:** Initial Production Release
- **v1.1.0:** Feature Update (Metrics and Dashboard improvements)
- **v1.2.0:** Performance & Release Tracking Update

See [RELEASING.md](file:///d:/me/MIT/Cloud-Technology/home_work_2/Homework3/RELEASING.md) for complete details.

---

## 4. How to Cut a Release

```bash
# 1. Commit changes
git add .
git commit -m "Release v1.2.0"

# 2. Create annotated tag
git tag -a v1.2.0 -m "Release version v1.2.0"

# 3. Push tag to GitHub
git push origin v1.2.0
```
GitHub's tag push webhook automatically triggers Jenkins to build, push to ECR, and deploy to Docker Swarm.

---

## 5. How to Trigger Rollback

If an issue occurs in `v1.2.0`, roll back to `v1.0.0` immediately without rebuilding:

1. Open Jenkins and navigate to the project pipeline.
2. Click **Build with Parameters**.
3. Set:
   - `ACTION`: `rollback`
   - `VERSION`: `v1.0.0`
4. Click **Build**.
5. Jenkins verifies the image `908157891706.dkr.ecr.us-east-1.amazonaws.com/sievphor-homework3:v1.0.0` in ECR and performs an immediate rolling update on Docker Swarm.

---

## 6. Amazon ECR Repository & Immutability
- **AWS Account ID:** `908157891706`
- **Region:** `us-east-1`
- **ECR Repository Name:** `sievphor-homework3`
- **Registry URI:** `908157891706.dkr.ecr.us-east-1.amazonaws.com/sievphor-homework3`
- **Retained Version Tags:**
  - `908157891706.dkr.ecr.us-east-1.amazonaws.com/sievphor-homework3:v1.0.0`
  - `908157891706.dkr.ecr.us-east-1.amazonaws.com/sievphor-homework3:v1.1.0`
  - `908157891706.dkr.ecr.us-east-1.amazonaws.com/sievphor-homework3:v1.2.0`

---

## 7. Deployment & Rollback Verification History

| Step | Version Tag | Action Executed | ECR Image Source | Swarm Result | Verification Status |
|---|---|---|---|---|---|
| 1 | `v1.0.0` | Initial Tag Deploy | Built & Pushed to ECR | 3/3 Replicas Active | Verified (HTTP 200) |
| 2 | `v1.1.0` | Minor Feature Release | Built & Pushed to ECR | Rolling Update Complete | Verified (HTTP 200) |
| 3 | `v1.2.0` | Latest Release | Built & Pushed to ECR | Rolling Update Complete | Verified (HTTP 200) |
| 4 | `v1.0.0` | **On-Demand Rollback** | **ECR Existing Tag (No Rebuild)** | **Swarm Reverted to v1.0.0** | **Rollback Verified** |

---

## 8. Live Application Endpoints
- **Manager:** `http://13.220.98.249:80`
- **Worker 1:** `http://34.229.219.41:80`
- **Worker 2:** `http://54.90.208.206:80`
- **Active Version at Submission:** `v1.0.0` (Demonstrating verified post-rollback state)
