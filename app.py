from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask import send_file
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
from PIL import Image
import os
from fpdf import FPDF
import datetime
from flask_cors import CORS
import google.generativeai as genai
import markdown2


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///malaria.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Load CNN model
model = load_model('malaria_cnn_model.keras')

# Create upload directory if not exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    symptoms = db.Column(db.String(500), nullable=False)
    ai_inference = db.Column(db.Text, nullable=True)  # Stores AI output
    final_diagnosis = db.Column(db.String(50), nullable=True)  # Stores CNN result
    image_path = db.Column(db.String(200), nullable=True)

with app.app_context():
    db.create_all()

# Image preprocessing for CNN
def preprocess_image(image_path):
    img = image.load_img(image_path, target_size=(128, 128))
    img_tensor = image.img_to_array(img)
    img_tensor = np.expand_dims(img_tensor, axis=0)
    img_tensor /= 255.
    return img_tensor


@app.route('/')
def index():
    return render_template('role_select.html')

CORS(app)
@app.template_filter('markdown')
def markdown_filter(text):
    return markdown2.markdown(text)

# Configure Gemma model via Google Generative AI
GOOGLE_API_KEY = "AIzaSyCZhNimZq820rBzxUi4VQQYIyIHIHsormY"  # 🔒 Replace with your actual key
genai.configure(api_key=GOOGLE_API_KEY)
MODEL_NAME = "gemma-3-4b-it"



# # Function: Send prompt to Gemma
# def generate_diagnosis(symptoms):
#     if not symptoms.strip():
#         return "No symptoms provided."

#     prompt = (
#         f"You are a smart AI medical assistant. A user describes these symptoms: {symptoms}. "
#         "Based on the symptoms, suggest the most likely disease and also recommend the type of medical specialist they should consult. "
#         "Give the probability that the disease can be a malaria infection. "
#         "Give the answer in the following format:\n"
#         "Probable Disease: <disease name>\n"
#         "Recommended Specialist: <type of specialist>\n"
#         "Probability of Malaria: <if high then suggest consult \n"
#     )

#     try:
#         model = genai.GenerativeModel(MODEL_NAME)
#         response = model.generate_content(prompt)
#         return response.text.strip() if response else "No diagnosis received."
#     except Exception as e:
#         return f"Error generating diagnosis: {str(e)}"


def generate_diagnosis(symptoms):
    if not symptoms.strip():
        return "No symptoms provided."

    # ---  Prompt ---
    prompt = (
        f"You are a helpful AI assistant for a malaria symptom checker. "
        f"You are NOT a medical doctor. Your purpose is to provide informational guidance, not a diagnosis. "
        f"A user has described the following symptoms: {symptoms}. "
        f"Based on this information, provide a structured response that:\n"
        f"1. Identifies the most likely conditions that could cause these symptoms. "
        f"2. Assesses the probability that the symptoms are related to malaria. "
        f"3. Recommends the type of medical specialist they should consult for an accurate diagnosis. "
        f"4. **Crucially, includes a clear, bold disclaimer at the end stating that this information is not a substitute for professional medical advice.**\n\n"
        f"Provide the response in the following format:\n"
        f"**Disclaimer:** This is for informational purposes only and is not a professional medical diagnosis. Always consult a qualified healthcare provider.\n\n"
        f"Format your answer in **Markdown** also format likely conditions in bullet points.\n"
        f"**Likely Conditions:**\n"
        f"<Condition 1>: <brief explanation>\n"
        f"<Condition 2>: <brief explanation>\n\n"
        f"**Malaria Probability:**\n"
        f"<A descriptive sentence assessing the probability, e.g., 'The probability of malaria is high, especially if you have traveled to an endemic area,' or 'The probability is low, as these symptoms are common to many viral infections."
        f"**Recommended Specialist:**\n"
        f"<Type of specialist, e.g., General Physician, Infectious Disease Specialist, etc.>\n"
        f"**Next Steps:**\n"
        f"<A simple, actionable instruction, such as 'Schedule an appointment with a doctor for a physical examination and a blood test.'>"
    )

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)

        # Check for empty response and return text
        if response and response.text:
            return response.text.strip()
        else:
            return "No diagnosis received."
    except Exception as e:
        return f"Error generating diagnosis: {str(e)}"

@app.route('/user-form', methods=['GET', 'POST'])
def user_form():
    if request.method == 'POST':
        # Get form fields
        name = request.form.get('name')
        age = request.form.get('age')
        gender = request.form.get('gender')
        mobile = request.form.get('mobile')
        symptoms = request.form.get('symptoms')

        # AI diagnosis
        ai_response = generate_diagnosis(symptoms)

        # Save to DB
        new_entry = Patient(
        name=name,
        age=int(age),
        gender=gender,
        mobile=mobile,
        symptoms=symptoms,
        ai_inference=ai_response,
        final_diagnosis=None,
        image_path=None
        )

        db.session.add(new_entry)
        db.session.commit()

        return render_template(
            'user_form.html',
            ai_response=ai_response,
            name=name,
            age=age,
            gender=gender,
            mobile=mobile,
            symptoms=symptoms
        )

    return render_template('user_form.html')

@app.route('/admin-dashboard')
def admin_dashboard():
    patients = Patient.query.all()
    return render_template('admin_dashboard.html', patients=patients)

@app.route('/admin/upload/<int:patient_id>', methods=['GET', 'POST'])
def admin_upload(patient_id):
    patient = Patient.query.get_or_404(patient_id)

    if request.method == 'POST':
        image = request.files.get('image')
        if image:
            filename = (image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)

            # Predict
            img_data = preprocess_image(image_path)
            pred_prob = model.predict(img_data)[0][0]
            diagnosis = 'Malaria Detected' if pred_prob <= 0.5 else 'No Malaria'

            # Save to DB
            patient.image_path = image_path
            patient.final_diagnosis = diagnosis
            db.session.commit()

            # For HTML display
            img_path_html = url_for('static', filename='uploads/' + filename)

            return render_template('admin_upload.html', patient=patient, prediction=diagnosis, img_path=img_path_html)

    # GET request
    return render_template('admin_upload.html', patient=patient)


@app.route('/generate-report/<int:patient_id>')
def generate_report(patient_id):
    patient = Patient.query.get_or_404(patient_id)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)

    # Header
    pdf.cell(200, 10, txt="Malaria Diagnostic Report", ln=True, align='C')
    pdf.ln(10)

    # Patient Info
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Name: {patient.name}", ln=True)
    pdf.cell(200, 10, txt=f"Age: {patient.age}", ln=True)
    pdf.cell(200, 10, txt=f"Gender: {patient.gender}", ln=True)
    pdf.cell(200, 10, txt=f"Mobile: {patient.mobile}", ln=True)
    pdf.multi_cell(0, 10, txt=f"Symptoms: {patient.symptoms}")
    pdf.ln(5)

    # Final Diagnosis (from slide image)
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, txt="Final Diagnosis (Slide Image):", ln=True)
    pdf.set_font("Arial", size=12)

    if patient.image_path:
        if patient.final_diagnosis and "Malaria Detected" in patient.final_diagnosis:
            final_diagnosis = "Malaria Detected"
        else:
            final_diagnosis = "No Malaria"
    else:
        final_diagnosis = "Pending (Image not uploaded)"

    pdf.multi_cell(0, 10, txt=final_diagnosis)
    pdf.ln(10)

    # Optional image
    if patient.image_path and os.path.exists(patient.image_path):
        pdf.image(patient.image_path, w=100)

    # Save PDF
    report_path = f"static/reports/report_{patient.id}.pdf"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    pdf.output(report_path)

    return send_file(report_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
