import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import os

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)

def create_report():
    doc = docx.Document()

    # Page Margins
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Title / Header
    p_uni = doc.add_paragraph()
    p_uni.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_uni = p_uni.add_run("សាកលវិទ្យាល័យ សៅស៍អុីសថ៍អេយេសៀ\nUNIVERSITY OF SOUTH-EAST ASIA\n")
    r_uni.font.name = 'Khmer OS Battambang'
    r_uni.font.size = Pt(14)
    r_uni.bold = True
    r_uni.font.color.rgb = RGBColor(16, 44, 87)

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_title.add_run("Homework 3\nRELEASE MANAGEMENT: GITHUB TAGS & JENKINS BUILD/PUSH/DEPLOY/ROLLBACK\n")
    r_title.font.name = 'Calibri'
    r_title.font.size = Pt(16)
    r_title.bold = True
    r_title.font.color.rgb = RGBColor(37, 99, 235)

    # Info Box Table
    info_table = doc.add_table(rows=6, cols=2)
    info_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    info_data = [
        ("Course:", "Advanced Cloud Technology"),
        ("Lecturer:", "Mr. Krol Noeurn"),
        ("Student Name:", "TONN Sievphor"),
        ("GitHub Repository:", "https://github.com/Sievphor/cloud_home_work_3.git"),
        ("Amazon ECR URI:", "908157891706.dkr.ecr.us-east-1.amazonaws.com/sievphor-homework3"),
        ("Academic Year:", "2026 - 2027")
    ]
    for i, (k, v) in enumerate(info_data):
        row = info_table.rows[i]
        c0, c1 = row.cells[0], row.cells[1]
        c0.text = k
        c1.text = v
        c0.paragraphs[0].runs[0].font.bold = True
        c0.paragraphs[0].runs[0].font.name = 'Calibri'
        c1.paragraphs[0].runs[0].font.name = 'Calibri'
        c0.width = Inches(2.2)
        c1.width = Inches(4.2)
        set_cell_background(c0, "F1F5F9")
        set_cell_background(c1, "F8FAFC")

    doc.add_page_break()

    def add_section_h1(text):
        h = doc.add_paragraph()
        r = h.add_run(text)
        r.font.name = 'Khmer OS Battambang'
        r.font.size = Pt(13)
        r.bold = True
        r.font.color.rgb = RGBColor(30, 58, 138)
        return h

    def add_body_p(text):
        p = doc.add_paragraph()
        r = p.add_run(text)
        r.font.name = 'Khmer OS Battambang'
        r.font.size = Pt(10.5)
        p.paragraph_format.line_spacing = 1.15
        return p

    # 1. Introduction
    add_section_h1("១. សេចក្តីផ្តើម (Introduction)")
    add_body_p(
        "កិច្ចការ Homework 3 ផ្តោតសំខាន់លើការគ្រប់គ្រងការបញ្ចេញកូដ (Release Management) ដោយប្រើប្រាស់ GitHub Tags "
        "និង Semantic Versioning (vMAJOR.MINOR.PATCH) នៅក្នុង Repository https://github.com/Sievphor/cloud_home_work_3.git។ "
        "ជំនួសឱ្យការ Deploy រាល់ពេលមាន Commit តូចតាច ប្រព័ន្ធ CI/CD របស់ Jenkins "
        "ដំណើរការតែនៅពេលមានការ Push Git Tag ប៉ុណ្ណោះ។ Docker Image ទាំងអស់ត្រូវបានដាក់ Tag ដូចគ្នានឹង Git Tag "
        "ហើយត្រូវបានរក្សាទុកជា Immutable Tags នៅក្នុង Amazon ECR (908157891706.dkr.ecr.us-east-1.amazonaws.com/sievphor-homework3)។ "
        "លើសពីនេះ ប្រព័ន្ធត្រូវបានបំពាក់នូវយន្តការ Rollback "
        "ដែលអនុញ្ញាតឱ្យត្រឡប់ទៅកាន់កំណែមុនបានភ្លាមៗ ដោយមិនបាច់ Build Image ឡើងវិញឡើយ។"
    )

    # 2. Objectives
    add_section_h1("២. គោលបំណង (Objectives)")
    add_body_p(
        "• អនុវត្ត Semantic Versioning (v1.0.0, v1.1.0, v1.2.0) ក្នុងការគ្រប់គ្រង Release\n"
        "• កំណត់ Jenkins Pipeline ឱ្យរត់តាម GitHub Tag Webhook (Tag-only trigger)\n"
        "• ធានាថា Docker Image Tag ត្រូវគ្នានឹង Git Tag និងរក្សាទុកគ្រប់រូបភាពទាំងអស់ក្នុង ECR\n"
        "• Parameterize Pipeline ជាមួយ ACTION (build, push, deploy, rollback) និង VERSION\n"
        "• អនុវត្ត Rollback ដោយទាញយក Image ចាស់ពី ECR មក Deploy លើ Docker Swarm ដោយគ្មាន Rebuild។"
    )

    # 3. Technology
    add_section_h1("៣. បច្ចេកវិទ្យា និងបរិស្ថាន (Technology & Environment)")
    add_body_p(
        "• GitHub & Git Tags: រក្សាទុក Source Code (cloud_home_work_3) និងកំណត់កំណែ Release\n"
        "• Jenkins: ស្វ័យប្រវត្តិកម្ម CI/CD Pipeline ជាមួយ Parameters\n"
        "• Docker & Amazon ECR: Build និងរក្សាទុក Versioned Container Images\n"
        "• Amazon EC2 & Docker Swarm: ដំណើរការសេវាកម្មជាមួយ Replicas ទាំង ៣ និង Rolling Update "
        "(Manager: 13.220.98.249, Worker 1: 34.229.219.41, Worker 2: 54.90.208.206)"
    )

    # 4. Implementation Steps
    add_section_h1("៤. ដំណើរការអនុវត្តជាក់ស្តែង (Implementation Steps)")
    add_body_p(
        "៤.១ ការបង្កើត Git Tags តាម Semantic Versioning:\n"
        "បានបង្កើត Releases ចំនួន ៣ រួមមាន v1.0.0, v1.1.0, និង v1.2.0 ដោយប្រើពាក្យបញ្ជា 'git tag -a <version> -m <msg>' "
        "និង Push ទៅកាន់ GitHub តាមរយៈ 'git push origin <version>'។"
    )
    add_body_p(
        "៤.២ ការកំណត់ Jenkins Parameterized Pipeline:\n"
        "Jenkinsfile ត្រូវបានរៀបចំឱ្យទទួល Parameters ACTION (build, push, deploy, rollback) "
        "និង VERSION សម្រាប់បញ្ជាក់ពីលេខ Tag។ នៅពេលមាន Tag Push មកដល់ Jenkins នឹង Build និង Deploy ដោយស្វ័យប្រវត្តិ។"
    )
    add_body_p(
        "៤.៣ ការរក្សាទុក Image ក្នុង Amazon ECR:\n"
        "រាល់ការ Build រូបភាពត្រូវបានដាក់ Tag ដូចគ្នានឹង Git Tag ហើយ Push ទៅ ECR Repository "
        "'908157891706.dkr.ecr.us-east-1.amazonaws.com/sievphor-homework3'។ គ្រប់ Tags ទាំងអស់ត្រូវបានរក្សាទុកដោយគ្មានការសរសេរជាន់លើ។"
    )
    add_body_p(
        "៤.៤ ការ Deploy លើ Docker Swarm:\n"
        "Jenkins ធ្វើបច្ចុប្បន្នភាពលើ Service 'homework3_web' តាមរយៈ Rolling Update (parallelism: 1, delay: 10s) "
        "ធានាថាកម្មវិធីនៅតែអាចចូលប្រើប្រាស់បានជានិច្ចអំឡុងពេល Deploy លើ Port 80។"
    )

    # 5. Rollback
    add_section_h1("៥. ការអនុវត្ត Rollback ដោយមិនបាច់ Rebuild")
    add_body_p(
        "នៅពេលមានបញ្ហាកើតឡើងលើកំណែ v1.2.0 យើងបានធ្វើការ Rollback ត្រឡប់ទៅកំណែ v1.0.0៖\n"
        "១. ដំណើរការ Jenkins Job ដោយជ្រើសរើស ACTION = rollback និង VERSION = v1.0.0\n"
        "២. Pipeline បានផ្ទៀងផ្ទាត់វត្តមានរបស់ Image v1.0.0 នៅក្នុង Amazon ECR ជាមុន\n"
        "៣. Jenkins បានបញ្ជាទៅ Swarm Manager (13.220.98.249) ឱ្យធ្វើ Rolling Update ទៅកាន់ Image v1.0.0 ផ្ទាល់\n"
        "៤. ដំណើរការនេះពុំមានការទាញយកកូដ ឬ Build រូបភាពថ្មីឡើយ (No Rebuild) ដែលជួយសន្សំពេលវេលា និងគ្មានហានិភ័យនៃកំហុសកូដ។"
    )

    # 6. Deployment History Table
    add_section_h1("៦. កំណត់ត្រាប្រវត្តិនៃការបញ្ចេញកូដ និង Rollback")
    
    table = doc.add_table(rows=5, cols=4)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Version", "Action", "Image Source", "Result"]
    for j, h in enumerate(headers):
        cell = table.rows[0].cells[j]
        cell.text = h
        cell.paragraphs[0].runs[0].font.bold = True
        cell.paragraphs[0].runs[0].font.name = 'Calibri'
        set_cell_background(cell, "E2E8F0")

    history_data = [
        ("v1.0.0", "Deploy Release", "Built & Pushed to ECR", "Success (Replicas 3/3)"),
        ("v1.1.0", "Deploy Release", "Built & Pushed to ECR", "Success (Rolling Update)"),
        ("v1.2.0", "Deploy Release", "Built & Pushed to ECR", "Success (Rolling Update)"),
        ("v1.0.0", "Rollback", "Direct from ECR (No Rebuild)", "Rollback Verified")
    ]
    for i, row_data in enumerate(history_data):
        row = table.rows[i + 1]
        for j, val in enumerate(row_data):
            cell = row.cells[j]
            cell.text = val
            cell.paragraphs[0].runs[0].font.name = 'Calibri'
            set_cell_background(cell, "F8FAFC" if i % 2 == 0 else "FFFFFF")

    # 7. Challenges & Solutions
    add_section_h1("៧. បញ្ហាប្រឈម និងដំណោះស្រាយ (Challenges & Solutions)")
    add_body_p(
        "• បញ្ហា Webhook ចាប់យក Push ធម្មតា៖ បានកំណត់ Branch Specifier ក្នុង Jenkins ទៅជា '*/tags/*' ដើម្បីឱ្យ Jenkins ចាប់តែ Tag Push។\n"
        "• បញ្ហា Worker Nodes មិនអាច Pull Private Image ពេល Rollback៖ បានបន្ថែមការផ្ញើ ECR Token ថ្មីទៅកាន់ Swarm Manager រាល់ពេល Rollback។\n"
        "• ជៀសវាងការ Rebuild កំឡុងពេល Rollback៖ បានបង្កើត Stage ដាច់ដោយឡែកសម្រាប់ Rollback ដែលរំលង Stage Checkout & Build ទាំងស្រុង។"
    )

    # 8. Conclusion
    add_section_h1("៨. សេចក្តីសន្និដ្ឋាន (Conclusion)")
    add_body_p(
        "កិច្ចការ Homework 3 នេះបានបង្ហាញពីប្រសិទ្ធភាពខ្ពស់នៃ Release Management ក្នុងប្រព័ន្ធ Cloud DevOps។ "
        "ការរួមបញ្ចូលគ្នារវាង Semantic Versioning, Immutable Image Tags ក្នុង Amazon ECR, Parameterized Jenkins Pipeline, "
        "និង Zero-Downtime Rollback លើ Docker Swarm ផ្តល់នូវស្តង់ដារវិស្វកម្មកម្រិត Production ដ៏រឹងមាំសម្រាប់គ្រប់គ្រងកម្មវិធី។\n"
        "• Manager Endpoint: http://13.220.98.249:80\n"
        "• Worker 1 Endpoint: http://34.229.219.41:80\n"
        "• Worker 2 Endpoint: http://54.90.208.206:80"
    )

    output_path = os.path.join(os.path.dirname(__file__), "TONN-Sievphor-Documentation_homework3.docx")
    doc.save(output_path)
    print(f"Successfully generated: {output_path}")

if __name__ == "__main__":
    create_report()
