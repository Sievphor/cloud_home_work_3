# សាកលវិទ្យាល័យ សៅស៍អុីសថ៍អេយេសៀ (UNIVERSITY OF SOUTH-EAST ASIA)
## មហាវិទ្យាល័យវិទ្យាសាស្ត្រ និងបច្ចេកវិទ្យា (Faculty of Science and Technology)

---

# Homework 3: Release Management: GitHub Tags & Jenkins Build/Push/Deploy/Rollback
### របាយការណ៍គ្រប់គ្រងការបញ្ចេញកូដ (Release Management) និងការវិលត្រឡប់ (Rollback) លើ AWS Cloud

- **Course:** Advanced Cloud Technology
- **Lecturer:** Mr. Krol Noeurn
- **Student Name:** TONN Sievphor
- **GitHub Repository:** https://github.com/Sievphor/cloud_home_work_3.git
- **Academic Year:** 2026 - 2027

---

## ១. សេចក្តីផ្តើម (Introduction)
នៅក្នុងប្រព័ន្ធ CI/CD ពិតប្រាកដរបស់ក្រុមហ៊ុនបច្ចេកវិទ្យា ការដាក់ពង្រាយ (Deploy) កម្មវិធីមិនត្រូវធ្វើឡើងរាល់ពេលមាន Commit តូចតាចនោះទេ ប៉ុន្តែត្រូវធ្វើឡើងតាមការកំណត់កាលបរិច្ឆេទបញ្ចេញច្បាស់លាស់ (Versioned Releases)។

Homework 3 នេះជាការបន្តពង្រីកសមត្ថភាពចេញពី Homework 2 ដោយបន្ថែមនូវវិន័យនៃការគ្រប់គ្រងការបញ្ចេញកូដ (Release Discipline)៖
1. Jenkins នឹងដំណើរការ Build និង Deploy ដោយស្វ័យប្រវត្តិតែនៅពេលមានការ Push Git Tag (`https://github.com/Sievphor/cloud_home_work_3.git`) ឧទាហរណ៍៖ `v1.0.0`, `v1.1.0`, `v1.2.0` ប៉ុណ្ណោះ មិនរត់តាម Push Commit ធម្មតាឡើយ។
2. រាល់ Docker Image ដែលត្រូវបាន Build ត្រូវតែមាន Tag ដូចគ្នាបេះបិទទៅនឹង Git Tag ហើយត្រូវបាន Push ទៅរក្សាទុកក្នុង Amazon ECR (`908157891706.dkr.ecr.us-east-1.amazonaws.com/sievphor-homework3`) ដោយមិនមានការសរសេរជាន់ (Never overwrite an existing tag)។
3. Jenkins Pipeline ត្រូវបានបំពាក់នូវ Parameters (`ACTION` និង `VERSION`) ដែលអនុញ្ញាតឱ្យអនុវត្តសកម្មភាព `build`, `push`, `deploy`, ឬ `rollback` តាមតម្រូវការ។
4. ការអនុវត្ត **Rollback** ត្រូវបានរៀបចំឡើងយ៉ាងមានប្រសិទ្ធភាព៖ ប្រព័ន្ធនឹងទាញយករូបភាព Image ចាស់ដែលធ្លាប់បាន Build រួចហើយនៅក្នុង ECR យកមក Deploy ផ្ទាល់នៅលើ Docker Swarm Cluster (Manager: 13.220.98.249, Worker 1: 34.229.219.41, Worker 2: 54.90.208.206) ដោយ**មិនចាំបាច់ Build Image ឡើងវិញឡើយ (No Rebuild)** និងប្រើប្រាស់ Swarm Rolling Update ដើម្បីធានាថាសេវាកម្មមិនដាច់ (Zero Downtime)។

---

## ២. គោលបំណង (Objectives)
- អនុវត្ត Semantic Versioning (`vMAJOR.MINOR.PATCH`) ក្នុងការគ្រប់គ្រងកំណែរបស់កម្មវិធី។
- កំណត់រចនាសម្ព័ន្ធ GitHub Tag Webhook ដើម្បី Trigger Jenkins Pipeline តែនៅពេលមាន Tag ថ្មី។
- ធានាភាពមិនអាចផ្លាស់ប្តូរបាន (Immutability) នៃ Docker Images នៅក្នុង Amazon ECR។
- Parameterize Jenkinsfile ដោយទទួលយក `ACTION` (all, build, push, deploy, rollback) និង `VERSION` (Git Tag)។
- អនុវត្តនិងផ្ទៀងផ្ទាត់ការធ្វើ Rollback ជាក់ស្តែងនៅលើ Production Service ដោយគ្មានការ Rebuild។

---

## ៣. បច្ចេកវិទ្យា និងបរិស្ថាន (Technology & Environment)

| បច្ចេកវិទ្យា (Technology) | តួនាទី និងភារកិច្ច (Role & Functionality) |
|---|---|
| **GitHub & Git Tags** | គ្រប់គ្រង Source Code (`cloud_home_work_3`) និងកំណត់ស្លាកកំណែ (Semantic Versioning Tags) |
| **Jenkins CI/CD** | ស្វ័យប្រវត្តិកម្ម Pipeline សម្រាប់ Build, Push, Deploy និង Rollback |
| **Docker & Buildx** | បង្កើត Multi-arch / AMD64 Image សម្រាប់ Production |
| **Amazon ECR** | ឃ្លាំងផ្ទុក Private Docker Images ដោយរក្សារាល់កំណែទាំងអស់ (v1.0.0, v1.1.0, v1.2.0) |
| **Amazon EC2** | ម៉ាស៊ីន Cloud Server សម្រាប់ដំណើរការ Jenkins និង Docker Swarm Cluster |
| **Docker Swarm** | ការគ្រប់គ្រង Service Replicas (3 Replicas) និងដំណើរការ Rolling Update / Rollback ដោយគ្មាន Downtime |

---

## ៤. ដំណើរការអនុវត្តជាក់ស្តែង (Implementation Workflow)

### ៤.១ កំណត់កំណែ Release ដោយប្រើ Semantic Versioning
- អនុវត្តតាមស្តង់ដារ `vMAJOR.MINOR.PATCH`៖
  - `v1.0.0`: Initial Release ដែលដាក់ពង្រាយលើ Docker Swarm
  - `v1.1.0`: Feature Release កែលម្អ UI Dashboard និង Metrics
  - `v1.2.0`: Performance & Logging Release
- បង្កើតឯកសារ `RELEASING.md` ដើម្បីពន្យល់ពីគោលការណ៍កំណត់កំណែ និងជំហាននៃការបញ្ចេញ Tag។
- ពាក្យបញ្ជាបង្កើត និង Push Git Tag៖
  ```bash
  git tag -a v1.0.0 -m "Release v1.0.0"
  git push origin v1.0.0
  ```

### ៤.២ កំណត់រចនាសម្ព័ន្ធ Jenkins Pipeline & Parameters
- កំណត់ Jenkinsfile ឱ្យទទួល Parameter ពីរគឺ៖
  - `ACTION`: `['all', 'build', 'push', 'deploy', 'rollback']`
  - `VERSION`: Git Tag គោលដៅ (ឧ. `v1.0.0`)
- កំណត់ SCM Refspec ក្នុង Jenkins Job:
  - Branch Specifier: `*/tags/*` ឬ `refs/tags/*`
  - ជួយឱ្យ Jenkins ចាប់យកតែ Tag Push Webhook ប៉ុណ្ណោះ។

### ៤.៣ Build និង Push Docker Image ទៅកាន់ Amazon ECR
- Jenkins នឹង Build រូបភាពដោយប្រើឈ្មោះពិតប្រាកដ៖
  `908157891706.dkr.ecr.us-east-1.amazonaws.com/sievphor-homework3:v1.0.0`
- Authenticate ទៅ ECR តាមរយៈ `aws ecr get-login-password` និង Push Image។
- ពិនិត្យបញ្ជាក់នៅក្នុង ECR ឃើញថា Image Tags `v1.0.0`, `v1.1.0`, និង `v1.2.0` ត្រូវបានរក្សាទុកទាំងអស់ដោយមិនមានការ Delete ឬ Overwrite ឡើយ។

### ៤.៤ Deploy ទៅកាន់ Docker Swarm Cluster
- Jenkins ភ្ជាប់ទៅកាន់ Swarm Manager លើ AWS EC2 (`13.220.98.249`)។
- ដំណើរការ Rolling Update ទៅកាន់ Service `homework3_web`៖
  ```bash
  docker service update \
    --with-registry-auth \
    --image 908157891706.dkr.ecr.us-east-1.amazonaws.com/sievphor-homework3:v1.2.0 \
    --update-parallelism 1 \
    --update-delay 10s \
    --update-failure-action rollback \
    homework3_web
  ```
- សេវាកម្មដំណើរការ Replicas ចំនួន ៣ (Manager, Worker 1, Worker 2) ដោយផ្លាស់ប្តូរម្តងមួយៗ ធានាថាកម្មវិធីនៅតែអាចចូលប្រើបានឥតឈប់ឈរ។

---

## ៥. ការអនុវត្ត Rollback ជាក់ស្តែង (Rollback Execution)

នៅពេលរកឃើញបញ្ហានៅលើកំណែ `v1.2.0` យើងបានអនុវត្តការ Rollback ត្រឡប់ទៅកាន់កំណែចាស់ `v1.0.0` ដូចខាងក្រោម៖

1. **ដំណើរការ Parameterized Build ក្នុង Jenkins:**
   - ជ្រើសរើស **Build with Parameters**
   - កំណត់ `ACTION = rollback`
   - កំណត់ `VERSION = v1.0.0`
   - ចុច **Build**

2. **ដំណាក់កាលត្រួតពិនិត្យ និង Deploy ដោយមិន Rebuild (No Rebuild Mechanism):**
   - Jenkins ដំណើរការ `aws ecr describe-images` ដើម្បីផ្ទៀងផ្ទាត់ថា Image `v1.0.0` មានវត្តមានស្រាប់នៅក្នុង ECR (`908157891706.dkr.ecr.us-east-1.amazonaws.com/sievphor-homework3`)។
   - **សំខាន់បំផុត:** គ្មានការទាញយកកូដមក Build ឡើងវិញឡើយ (No buildx step)!
   - Jenkins បញ្ជូន Token ទៅកាន់ Swarm Manager (`13.220.98.249`) ហើយបញ្ជាឱ្យ Service ទាញយក Image `v1.0.0` ពី ECR ដោយផ្ទាល់។
   - Swarm ធ្វើការ Rolling Rollback ទៅកាន់កំណែ `v1.0.0` យ៉ាងលឿនក្នុងរយៈពេលត្រឹមតែប៉ុន្មានវិនាទី។

---

## ៦. កំណត់ត្រាប្រវត្តិនៃការ Deploy និង Rollback (Deployment & Rollback History)

| ល.រ | កំណែ (Version) | សកម្មភាព (Action) | ប្រភពរូបភាព (Image Source) | ស្ថានភាព (Status) |
|---|---|---|---|---|
| ១ | `v1.0.0` | Initial Release | Build & Push to ECR | Success (Replicas 3/3) |
| ២ | `v1.1.0` | Feature Release | Build & Push to ECR | Success (Rolling Update) |
| ៣ | `v1.2.0` | Latest Release | Build & Push to ECR | Success (Rolling Update) |
| ៤ | `v1.0.0` | **Rollback Execution** | **Direct from ECR (No Rebuild)** | **Rollback Verified Success** |

---

## ៧. បញ្ហាប្រឈម និងដំណោះស្រាយ (Challenges & Solutions)

| បញ្ហាប្រឈម (Challenges) | មូលហេតុ (Root Causes) | ដំណោះស្រាយ (Solutions) |
|---|---|---|
| **Jenkins Trigger រាល់ Push ធម្មតា** | Webhook មិនបានបែងចែក Push Event និង Tag Push | កំណត់ Refspec ទៅ `+refs/tags/*:refs/remotes/origin/tags/*` និង Branch Specifier `*/tags/*` |
| **Rollback ចំណាយពេលយូរ ឬបរាជ័យ** | Pipeline បែរជាទៅ Build កូដឡើងវិញនាំឱ្យខូច Version | បង្កើត Stage ដាច់ដោយឡែកសម្រាប់ `rollback` ដែលរំលង Stage `Build` និងផ្ទៀងផ្ទាត់ ECR ជាមុន |
| **Worker Nodes មិនអាច Pull Private Image ពេល Rollback** | Swarm Nodes អស់សុពលភាព ECR Authentication Token | បញ្ជូន ECR Login Token ថ្មីពី Jenkins ទៅកាន់ Manager Node រាល់ពេល Rollback |

---

## ៨. សេចក្តីសន្និដ្ឋាន (Conclusion)
ការអនុវត្ត Homework 3 នេះបានបង្ហាញពីសារៈសំខាន់នៃ Release Discipline នៅក្នុងវិស្វកម្ម Cloud DevOps៖
- ការប្រើប្រាស់ Semantic Versioning ធ្វើឱ្យការបញ្ចេញកូដមានភាពច្បាស់លាស់ ងាយស្រួលតាមដាន និងជៀសវាងការច្រឡំ។
- ការរក្សាទុក Docker Images ជាលក្ខណៈ Immutable Tags ក្នុង Amazon ECR ផ្តល់នូវទំនុកចិត្តខ្ពស់ក្នុងការគ្រប់គ្រង Artefacts។
- យន្តការ Rollback ដោយមិនបាច់ Rebuild គឺជាកត្តាស្នូលសម្រាប់ធានា Business Continuity និង High Availability នៅពេលមានអាសន្នលើ Production Environment។
- កម្មវិធីអាចចូលមើលបានជាក់ស្តែងតាមរយៈ៖
  - Manager: `http://13.220.98.249:80`
  - Worker 1: `http://34.229.219.41:80`
  - Worker 2: `http://54.90.208.206:80`
