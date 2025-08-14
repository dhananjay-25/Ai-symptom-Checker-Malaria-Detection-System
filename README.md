# 🩺 AI Symptom Checker + Malaria Detection System

## 📌 Overview
This project is a **dual-function healthcare application** combining **Generative AI** and **Deep Learning** for improved disease detection.  
It provides:
1. **AI Symptom Checker** – Analyzes patient-reported symptoms using **Google’s Gemma-3-4B-IT** Generative AI model to suggest probable conditions and recommend medical specialists.
2. **Malaria Detection** – Uses a **custom-trained CNN** to detect malaria from microscopic blood smear images uploaded by doctors.

The system is designed with a **clear separation** between AI-assisted initial assessment and **laboratory-confirmed** medical diagnosis.

---

## 🎯 Objectives
- Provide **early AI-based health assessment** based on patient symptoms.
- Allow **doctors to confirm malaria** via blood smear image classification.
- Maintain **secure and scalable architecture** with clear role separation (User & Doctor/Admin).
- Automate **medical report generation** in PDF format.

---

## 🛠️ Tech Stack
**Frontend:**
- HTML5, CSS3, Bootstrap 5
- Jinja2 templating (Flask)

**Backend:**
- Flask (Python)
- SQLAlchemy ORM with SQLite database
- Google Generative AI API (Gemma-3-4B-IT model)

**Machine Learning:**
- **Generative AI:** `gemma-3-4b-it` for symptom analysis
- **CNN Model:** Custom-trained on malaria blood smear dataset (binary classification: Parasitized / Uninfected)

**Other:**
- FPDF for automated PDF medical reports
- Werkzeug for secure file uploads

---

## 🧠 AI Symptom Checker (Generative AI)
- **Model:** Google’s `gemma-3-4b-it`
- **Function:** Takes patient symptoms (free text), generates:
  - Likely conditions (bullet-point list, markdown format)
  - Recommended type of medical specialist
- **Prompt Engineering:** Optimized for structured output without disclaimers in admin view
- **Note:** AI output is **not a medical verdict**, only an initial advisory

---

## 🦠 Malaria Detection (CNN Model)
- **Architecture:** Sequential CNN with Conv2D, MaxPooling, Flatten, Dense, Dropout layers
- **Training Dataset:** Microscopic malaria cell images
- **Image Input Size:** 128×128 pixels (RGB)
- **Preprocessing:** Normalized pixel values (`/255.0`)
- **Loss Function:** Binary Crossentropy
- **Optimizer:** Adam
- **Output Classes:** 
  - `Malaria Detected`
  - `No Malaria`
- **Purpose:** Provides the **final medical diagnosis** when slide image is uploaded by doctor

---

## 🗄️ Database Schema
**Patient Table**
| Field         | Type     | Description |
|--------------|----------|-------------|
| id           | Integer  | Primary key |
| name         | String   | Patient name |
| age          | Integer  | Age |
| gender       | String   | Male/Female |
| mobile       | String   | Contact number |
| symptoms     | String   | Entered symptoms |
| ai_inference | Text     | AI-generated probable conditions |
| image_path   | String   | Path to uploaded malaria slide |
| diagnosis    | String   | Final malaria detection result |

---

## 📂 Features

### 👤 **User Module**
- Enter symptoms in natural language
- View AI-generated probable conditions & recommended specialist
- Download **PDF report** containing:
  - Personal details
  - Symptoms
  - Final doctor-confirmed diagnosis

### 🩺 **Admin (Doctor) Module**
- View patient submissions with AI inference
- Upload malaria slide images for CNN-based diagnosis
- Update and finalize diagnosis in database
- Generate and download patient PDF reports

---

## ⚙️ System Workflow

1. **Patient Submits Symptoms** → Stored in database → AI model processes symptoms → Displays AI inference to patient
2. **Doctor Views Case** → Uploads malaria slide → CNN model runs diagnosis → Updates patient record with final result
3. **Generate PDF Report** → Includes patient details, AI inference, and **final confirmed diagnosis**

---

## 🚀 Setup & Installation

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/malaria-ai-symptom-checker.git
cd malaria-ai-symptom-checker
