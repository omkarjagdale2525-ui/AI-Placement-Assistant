from flask import Flask, render_template, request, make_response
from reportlab.pdfgen import canvas
from io import BytesIO
from groq import Groq
import os

app = Flask(__name__)
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)
resume_data = {}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/resume")
def resume():
    return render_template("resume.html")

@app.route("/generate_resume", methods=["POST"])
def generate_resume():
    global resume_data

    resume_data = {
        "name": request.form["name"],
        "email": request.form["email"],
        "phone": request.form["phone"],
        "linkedin": request.form["linkedin"],
        "education": request.form["education"],
        "skills": request.form["skills"],
        "projects": request.form["projects"],
        "certifications": request.form["certifications"]
    }

    return render_template("generated_resume.html", **resume_data)

@app.route("/download_resume")
def download_resume():
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)

    y = 800

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, y, resume_data["name"])
    y -= 25

    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, y, f'{resume_data["phone"]} | {resume_data["email"]} | {resume_data["linkedin"]}')
    y -= 40

    sections = {
        "Professional Summary": f'Motivated IT graduate with technical skills in {resume_data["skills"]}. Experienced in academic and personal projects with strong problem-solving and teamwork abilities.',
        "Education": resume_data["education"],
        "Technical Skills": resume_data["skills"],
        "Projects": resume_data["projects"],
        "Certifications": resume_data["certifications"]
    }

    for title, content in sections.items():
        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawString(50, y, title)
        y -= 20

        pdf.setFont("Helvetica", 10)

        for line in content.split("\n"):
            clean_line = line.replace("•", "-").replace("–", "-")
            pdf.drawString(60, y, clean_line[:90])
            y -= 15

            if y < 80:
                pdf.showPage()
                y = 800

        y -= 15

    pdf.save()
    buffer.seek(0)

    response = make_response(buffer.getvalue())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "attachment; filename=generated_resume.pdf"

    return response

@app.route("/ats", methods=["GET", "POST"])
def ats_checker():
    score = None
    suggestions = []
    strengths = []
    level = ""
    score_color = "primary"

    if request.method == "POST":
        resume_text = request.form["resume_text"].lower()
        role = request.form["role"].lower()
        score = 0

        basic_checks = {
            "Email": ("email" in resume_text or "@" in resume_text, 10),
            "Phone Number": ("phone" in resume_text or any(char.isdigit() for char in resume_text), 10),
            "Education": ("education" in resume_text or "bachelor" in resume_text or "b.sc" in resume_text, 10),
            "Skills Section": ("skills" in resume_text or "technical skills" in resume_text, 10),
            "Projects": ("project" in resume_text or "projects" in resume_text, 10),
            "Certifications": ("certification" in resume_text or "certifications" in resume_text, 10),
            "LinkedIn": ("linkedin" in resume_text, 5),
            "GitHub": ("github" in resume_text, 5)
        }

        role_keywords = {
            "software developer": ["python", "java", "html", "css", "javascript", "sql", "mysql", "oop", "github", "api"],
            "python developer": ["python", "flask", "sql", "mysql", "api", "oop", "github", "html", "css"],
            "web developer": ["html", "css", "javascript", "php", "bootstrap", "mysql", "responsive", "github"],
            "data analyst": ["excel", "power bi", "sql", "data analytics", "dashboard", "visualization", "python", "dax"],
            "it support": ["linux", "windows", "troubleshooting", "network", "hardware", "software", "technical support"]
        }

        for check, (passed, points) in basic_checks.items():
            if passed:
                score += points
                strengths.append(f"{check} found")
            else:
                suggestions.append(f"Add {check}")

        selected_keywords = role_keywords.get(role, [])

        matched_keywords = []
        missing_keywords = []

        for keyword in selected_keywords:
            if keyword in resume_text:
                matched_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)

        score += len(matched_keywords) * 3

        if score > 100:
            score = 100

        for keyword in matched_keywords:
            strengths.append(f"Keyword matched: {keyword}")

        for keyword in missing_keywords[:6]:
            suggestions.append(f"Add keyword: {keyword}")

        if score >= 85:
            level = "Excellent ATS Match"
            score_color = "success"
        elif score >= 70:
            level = "Good ATS Match"
            score_color = "primary"
        elif score >= 50:
            level = "Average ATS Match"
            score_color = "warning"
        else:
            level = "Needs Improvement"
            score_color = "danger"

    return render_template(
        "ats.html",
        score=score,
        strengths=strengths,
        suggestions=suggestions,
        level=level,
        score_color=score_color
    )

@app.route("/interview", methods=["GET", "POST"])
def interview():
    questions = []
    subject = ""
    difficulty = ""

    question_bank = {
        "python": {
            "easy": [
                ("What is Python?", "Python is a high-level, interpreted programming language."),
                ("What is a variable?", "A variable stores data values."),
                ("What is a list?", "A list stores multiple items in a single variable.")
            ],
            "medium": [
                ("What is the difference between list and tuple?", "List is mutable, tuple is immutable."),
                ("What is a function?", "A reusable block of code."),
                ("What is exception handling?", "Handling runtime errors using try and except.")
            ],
            "hard": [
                ("What is OOP?", "Object-Oriented Programming uses classes and objects."),
                ("What is Flask?", "Flask is a lightweight Python web framework."),
                ("What are decorators?", "Decorators modify function behavior without changing its code.")
            ]
        },

        "sql": {
            "easy": [
                ("What is SQL?", "SQL is used to manage relational databases."),
                ("What is a table?", "A table stores data in rows and columns."),
                ("What is a primary key?", "It uniquely identifies each record.")
            ],
            "medium": [
                ("What is JOIN?", "JOIN combines rows from multiple tables."),
                ("What is GROUP BY?", "It groups rows with similar values."),
                ("What is a foreign key?", "It links one table to another.")
            ],
            "hard": [
                ("What is normalization?", "Organizing data to reduce redundancy."),
                ("What is indexing?", "Indexing improves query performance."),
                ("What is a stored procedure?", "A reusable SQL block stored in the database.")
            ]
        },

        "dbms": {
            "easy": [
                ("What is DBMS?", "A system used to store and manage data."),
                ("What is a database?", "An organized collection of data."),
                ("What is data?", "Raw facts and figures.")
            ],
            "medium": [
                ("What is normalization?", "Reducing redundancy in data."),
                ("What is ER diagram?", "A diagram showing entities and relationships."),
                ("What is a transaction?", "A group of database operations.")
            ],
            "hard": [
                ("What are ACID properties?", "Atomicity, Consistency, Isolation, Durability."),
                ("What is deadlock?", "When processes wait for each other forever."),
                ("What is concurrency control?", "Managing simultaneous database operations.")
            ]
        },

        "os": {
            "easy": [
                ("What is an operating system?", "Software that manages hardware and software resources."),
                ("What is a process?", "A program in execution."),
                ("What is memory management?", "Managing computer memory efficiently.")
            ],
            "medium": [
                ("What is multitasking?", "Running multiple tasks at the same time."),
                ("What is scheduling?", "Deciding which process runs next."),
                ("What is virtual memory?", "Using disk space as extra memory.")
            ],
            "hard": [
                ("What is deadlock?", "A condition where processes wait forever."),
                ("What is paging?", "Dividing memory into fixed-size pages."),
                ("What is a semaphore?", "A synchronization tool used in OS.")
            ]
        },

        "cn": {
            "easy": [
                ("What is a computer network?", "A group of connected computers sharing resources."),
                ("What is IP address?", "A unique address assigned to a device on a network."),
                ("What is LAN?", "Local Area Network used in a small area.")
            ],
            "medium": [
                ("What is TCP?", "A reliable communication protocol."),
                ("What is UDP?", "A faster but less reliable protocol."),
                ("What is DNS?", "It converts domain names into IP addresses.")
            ],
            "hard": [
                ("What is OSI model?", "A 7-layer model for network communication."),
                ("What is subnetting?", "Dividing a network into smaller networks."),
                ("What is firewall?", "A security system that monitors network traffic.")
            ]
        },

        "web": {
            "easy": [
                ("What is HTML?", "HTML structures web pages."),
                ("What is CSS?", "CSS styles web pages."),
                ("What is JavaScript?", "JavaScript adds interactivity to web pages.")
            ],
            "medium": [
                ("What is responsive design?", "Design that works on different screen sizes."),
                ("What is Bootstrap?", "A CSS framework for responsive websites."),
                ("What is DOM?", "Document Object Model represents page structure.")
            ],
            "hard": [
                ("What is event bubbling?", "Events move from child to parent elements."),
                ("What is async JavaScript?", "JavaScript that runs without blocking execution."),
                ("What is API integration?", "Connecting frontend/backend with external services.")
            ]
        },

        "php": {
            "easy": [
                ("What is PHP?", "PHP is a server-side scripting language."),
                ("What is echo in PHP?", "It displays output."),
                ("What is a PHP variable?", "A variable stores data using the $ symbol.")
            ],
            "medium": [
                ("What is POST method?", "Used to send form data securely."),
                ("What is SESSION?", "It stores user data across pages."),
                ("What is include in PHP?", "It includes another PHP file.")
            ],
            "hard": [
                ("What is PDO?", "A secure way to connect PHP with databases."),
                ("What is SQL injection?", "A database attack using malicious SQL."),
                ("How do you prevent SQL injection?", "Use prepared statements.")
            ]
        },

        "linux": {
            "easy": [
                ("What is Linux?", "An open-source operating system."),
                ("What is the ls command?", "It lists files and folders."),
                ("What is pwd?", "It shows the current directory.")
            ],
            "medium": [
                ("What is chmod?", "It changes file permissions."),
                ("What is sudo?", "It runs commands with admin privileges."),
                ("What is grep?", "It searches text patterns.")
            ],
            "hard": [
                ("What is shell scripting?", "Writing scripts to automate Linux tasks."),
                ("What is cron job?", "A scheduled task in Linux."),
                ("What is process management?", "Managing running processes using commands like ps and kill.")
            ]
        },

        "data analytics": {
            "easy": [
                ("What is data analytics?", "The process of analyzing data to find useful insights."),
                ("What is Excel used for?", "Data cleaning, calculations, and analysis."),
                ("What is Power BI?", "A tool for creating dashboards and reports.")
            ],
            "medium": [
                ("What is data visualization?", "Representing data using charts and graphs."),
                ("What is DAX?", "A formula language used in Power BI."),
                ("What is data cleaning?", "Removing errors and inconsistencies from data.")
            ],
            "hard": [
                ("What is KPI?", "A key performance indicator used to measure performance."),
                ("What is ETL?", "Extract, Transform, Load process."),
                ("What is dashboarding?", "Creating visual reports for decision-making.")
            ]
        },

        "hr": {
            "easy": [
                ("Tell me about yourself.", "I am a B.Sc. IT graduate with skills in Python, SQL, web development, and AI-based projects."),
                ("What are your strengths?", "My strengths are quick learning, problem solving, communication, and adaptability."),
                ("Why should we hire you?", "I have the required technical foundation, project experience, and willingness to learn.")
            ],
            "medium": [
                ("Why do you want this role?", "This role matches my skills and gives me an opportunity to grow as a software professional."),
                ("Where do you see yourself in 5 years?", "I see myself as a skilled software developer contributing to meaningful projects."),
                ("How do you handle pressure?", "I break tasks into smaller steps, prioritize work, and stay focused.")
            ],
            "hard": [
                ("Why should we hire a fresher?", "Freshers bring energy, adaptability, and willingness to learn new technologies."),
                ("Describe a challenge you faced.", "I faced technical issues while building projects, researched solutions, and improved my debugging skills."),
                ("Why do you want to join our company?", "I want to join a company where I can learn, contribute, and grow professionally.")
            ]
        }
    }

    if request.method == "POST":
        subject = request.form["subject"].lower()
        difficulty = request.form["difficulty"].lower()
        questions = question_bank.get(subject, {}).get(difficulty, [])

    return render_template(
        "interview.html",
        questions=questions,
        subject=subject,
        difficulty=difficulty
    )
@app.route("/cover_letter", methods=["GET", "POST"])
def cover_letter():
    generated_letter = ""

    if request.method == "POST":
        name = request.form["name"]
        company = request.form["company"]
        role = request.form["role"]
        skills = request.form["skills"]

        generated_letter = f"""
Dear Hiring Manager,

I am writing to express my interest in the {role} position at {company}. My name is {name}, and I have developed a strong foundation in {skills} through academic learning, certifications, and hands-on projects.

I am passionate about technology and eager to begin my professional journey with an organization like {company}. My project experience has helped me strengthen my problem-solving, technical, and communication skills.

I believe my willingness to learn, adaptability, and dedication to quality work make me a suitable candidate for the {role} role. I would be grateful for the opportunity to contribute to your team and grow as a professional.

Thank you for your time and consideration.

Sincerely,
{name}
"""

    return render_template("cover_letter.html", generated_letter=generated_letter)
@app.route("/download_cover_letter")
def download_cover_letter():

    letter = request.args.get("letter", "")

    # Fix missing spaces after punctuation
    letter = letter.replace(".", ".\n\n")
    letter = letter.replace(",", ", ")

    buffer = BytesIO()
    p = canvas.Canvas(buffer)

    x = 60
    y = 780
    max_chars = 80

    p.setFont("Helvetica-Bold", 18)
    p.drawString(x, y, "Cover Letter")
    y -= 50

    p.setFont("Helvetica", 11)

    paragraphs = letter.split("\n\n")

    for paragraph in paragraphs:
        paragraph = paragraph.strip()

        if not paragraph:
            continue

        words = paragraph.split()
        line = ""

        for word in words:
            if len(line + " " + word) <= max_chars:
                line += " " + word
            else:
                p.drawString(x, y, line.strip())
                y -= 18
                line = word

        if line:
            p.drawString(x, y, line.strip())
            y -= 28

    p.save()
    buffer.seek(0)

    response = make_response(buffer.getvalue())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "attachment; filename=Omkar_Cover_Letter.pdf"

    return response
@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    quiz_questions = []
    score = None
    total = 0
    percentage = 0
    selected_subject = ""

    quiz_bank = {
        "python": [
            {
                "question": "What is Python?",
                "options": ["Programming Language", "Database", "Operating System", "Browser"],
                "answer": "Programming Language"
            },
            {
                "question": "Which symbol is used for comments in Python?",
                "options": ["//", "#", "/* */", "--"],
                "answer": "#"
            },
            {
                "question": "Which data type stores multiple values?",
                "options": ["int", "float", "list", "string"],
                "answer": "list"
            }
        ],
        "sql": [
            {
                "question": "What does SQL stand for?",
                "options": ["Structured Query Language", "Simple Query Language", "System Query Logic", "Server Query List"],
                "answer": "Structured Query Language"
            },
            {
                "question": "Which command is used to fetch data?",
                "options": ["GET", "SELECT", "FETCH", "SHOW"],
                "answer": "SELECT"
            },
            {
                "question": "Which keyword removes duplicate records?",
                "options": ["UNIQUE", "DISTINCT", "DELETE", "REMOVE"],
                "answer": "DISTINCT"
            }
        ],
        "dbms": [
            {
                "question": "What is DBMS?",
                "options": ["Database Management System", "Data Backup Management Software", "Digital Base Machine System", "Database Machine Software"],
                "answer": "Database Management System"
            },
            {
                "question": "Which key uniquely identifies a record?",
                "options": ["Foreign Key", "Primary Key", "Candidate Key", "Super Key"],
                "answer": "Primary Key"
            },
            {
                "question": "What does ACID stand for?",
                "options": ["Atomicity Consistency Isolation Durability", "Access Control Internet Data", "Automatic Code Input Data", "Advanced Computer Internal Database"],
                "answer": "Atomicity Consistency Isolation Durability"
            }
        ]
    }

    if request.method == "POST":
        selected_subject = request.form["subject"]
        quiz_questions = quiz_bank.get(selected_subject, [])

        if "submit_quiz" in request.form:
            total = len(quiz_questions)
            score = 0

            for i, q in enumerate(quiz_questions):
                user_answer = request.form.get(f"question_{i+1}")
                if user_answer == q["answer"]:
                    score += 1

            percentage = round((score / total) * 100, 2) if total > 0 else 0

    return render_template(
        "quiz.html",
        quiz_questions=quiz_questions,
        score=score,
        total=total,
        percentage=percentage,
        selected_subject=selected_subject
    )
@app.route("/dashboard")
def dashboard():
    stats = {
        "resumes_created": 1,
        "ats_score": 85,
        "interview_questions": 30,
        "quizzes_completed": 1,
        "cover_letters": 1,
        "placement_readiness": 82
    }

    return render_template("dashboard.html", stats=stats)
@app.route("/improve_resume", methods=["GET", "POST"])
def improve_resume():

    ai_result = ""

    if request.method == "POST":
        resume_text = request.form["resume_text"]

        prompt = f"""
Improve this resume content for ATS and software developer roles.
Give clear suggestions in sections:
1. Skills Improvement
2. Project Improvement
3. Profile Summary Improvement
4. Keywords to Add

Resume:
{resume_text}
"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        ai_result = response.choices[0].message.content

    return render_template(
        "improve_resume.html",
        ai_result=ai_result
    )
@app.route("/job_match", methods=["GET", "POST"])
def job_match():
    match_score = None
    missing_keywords = []
    matched_keywords = []
    suggestions = []
    score_color = "primary"
    recommendation = ""

    if request.method == "POST":
        resume_text = request.form["resume_text"].lower()
        job_description = request.form["job_description"].lower()

        important_keywords = [
            "python", "sql", "flask", "api", "mysql", "javascript",
            "html", "css", "git", "github", "power bi", "excel",
            "communication", "problem solving", "teamwork", "linux",
            "rest api", "database", "bootstrap"
        ]

        for keyword in important_keywords:
            if keyword in job_description:
                if keyword in resume_text:
                    matched_keywords.append(keyword)
                else:
                    missing_keywords.append(keyword)

        total_keywords = len(matched_keywords) + len(missing_keywords)

        if total_keywords > 0:
            match_score = round((len(matched_keywords) / total_keywords) * 100, 2)
        else:
            match_score = 0

        if match_score >= 80:
            score_color = "success"
            recommendation = "Strong Match for this role."
            suggestions.append("Your resume matches most required keywords.")
        elif match_score >= 50:
            score_color = "warning"
            recommendation = "Good Match, but improvement needed."
            suggestions.append("Add missing keywords naturally in Skills, Projects, or Summary.")
        else:
            score_color = "danger"
            recommendation = "Low Match. Resume customization required."
            suggestions.append("Customize your resume according to this job description.")

        if missing_keywords:
            suggestions.append("Add the missing keywords where they are honestly relevant.")

    return render_template(
        "job_match.html",
        match_score=match_score,
        missing_keywords=missing_keywords,
        matched_keywords=matched_keywords,
        suggestions=suggestions,
        score_color=score_color,
        recommendation=recommendation
    )
if __name__ == "__main__":
    app.run(debug=True)