# 🕵️ CyberCase AI – Digital Crime Scene Investigator

CyberCase AI is an AI-assisted digital investigation web application designed to help organize and analyze digital evidence during cybersecurity investigations.

The system provides a centralized dashboard for managing investigation cases, analyzing suspicious patterns, viewing evidence timelines, generating risk assessments, and creating investigation reports.

> ⚠️ **Disclaimer:** CyberCase AI is an educational and portfolio project. It does not perform real criminal identification, authenticate forensic evidence, or provide legal/forensic conclusions.

---

## 🚀 Features

- 📁 **Digital Case Management**
  - Create and manage investigation cases
  - Store case information in SQLite

- 🔍 **Evidence Analysis**
  - Analyze uploaded/recorded evidence information
  - Identify suspicious patterns and activity indicators

- 🤖 **AI/ML Risk Analysis**
  - Uses Machine Learning to analyze investigation signals
  - Generates a risk assessment based on available evidence

- 📊 **Investigation Dashboard**
  - View case statistics
  - Monitor risk levels
  - Display suspicious activity indicators

- 🕒 **Evidence Timeline**
  - Organize investigation events chronologically
  - Track important evidence-related activities

- 🚨 **Suspicious Activity Detection**
  - Highlights potentially suspicious signals
  - Provides investigation indicators for further review

- 📄 **Investigation Report**
  - Generate a PDF investigation report
  - Summarize case information and analysis results

- 🗄️ **SQLite Database**
  - Stores case and investigation information locally

- 🌐 **Responsive Web Interface**
  - Dark cybersecurity-themed interface
  - Built using HTML, CSS and JavaScript

---

## 🛠️ Technologies Used

### Frontend
- HTML5
- CSS3
- JavaScript

### Backend
- Python
- Flask

### Database
- SQLite

### Machine Learning
- Scikit-learn
- NumPy

### Report Generation
- ReportLab

---

## 🏗️ Project Architecture

```text
                 ┌─────────────────────┐
                 │    Web Dashboard    │
                 │   HTML/CSS/JS       │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │     Flask API       │
                 │      Backend        │
                 └──────────┬──────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
        ┌──────────┐  ┌───────────┐  ┌────────────┐
        │ SQLite   │  │ AI / ML   │  │ Evidence   │
        │ Database │  │ Analysis  │  │ Timeline   │
        └──────────┘  └───────────┘  └────────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Investigation Report│
                 │       (PDF)         │
                 └─────────────────────┘
