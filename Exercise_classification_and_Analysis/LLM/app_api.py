from flask import Flask, request, jsonify
import os
import json
import re
from werkzeug.utils import secure_filename
import google.generativeai as genai
from dotenv import load_dotenv
from mediapipe_utils.rep_counter import analyze_with_mediapipe

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'webm'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

analysis_cache = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def input_video_setup(file_path, mime_type):
    with open(file_path, "rb") as f:
        return {
            "mime_type": mime_type,
            "data": f.read()
        }

input_prompt = """
You are a certified fitness trainer and kinesiologist specializing in video-based workout recognition, form analysis, and repetition counting.  
Given the video below, analyze the visible workout activity and provide a comprehensive breakdown. Use biomechanical analysis and visual estimation techniques to determine exercise type, form quality, and number of repetitions. Your response must strictly follow the JSON format outlined below—no extra text, disclaimers, or explanations.

Format:
{
    "exercise_name": "detected workout name (e.g., push-up, squat)",
    "repetitions": number,  // total complete reps detected
    "calories_burned": number,  // estimated calories burned based on exercise type, duration, and intensity
    "form_analysis": {
        "posture": "comment on body alignment, back position, etc.",
        "range_of_motion": "describe depth or extension quality",
        "tempo": "comment on the speed of each rep",
        "common_mistakes": [
            "brief note on any form mistakes (if any)",
            ...
        ]
    },
    "performance_score": number,  // score out of 10 evaluating form and consistency
    "encouragement_and_tips": {
        "positive_feedback": [
            "💪 Great control during [specific aspect]!",
            "🌟 Impressive consistency in [highlighted strength]!"
        ],
        "improvement_tips": [
            "🛠 Try to maintain [suggestion] for better form.",
            "📏 Improve [specific mistake] to enhance results."
        ],
        "context": "Start by highlighting strengths in form or effort. Then, give 1–2 clear, actionable tips for improvement. Use fitness-positive emojis such as 💪 for strength, 📏 for form, 🏋️ for lifting, 🧘 for balance, 🛠 for corrections."
    }
}
Only output valid JSON. Do not include any other explanatory or introductory content."""  # (Use same prompt from earlier version, unchanged)


def get_gemini_response(input, vid_file, prompt):
    model = genai.GenerativeModel('gemini-2.0-flash-lite', generation_config={'temperature': 0.0})
    response = model.generate_content([input, vid_file, prompt])
    return response.text

def clean_and_parse_response(response_text):
    match = re.search(r"```json(.*?)```", response_text, re.DOTALL)
    cleaned_json = match.group(1).strip() if match else re.search(r"\{.*\}", response_text, re.DOTALL).group(0).strip()
    return json.loads(cleaned_json)

@app.route('/analyze', methods=['POST'])
def analyze_video():
    print("Request.files keys:", list(request.files.keys()))
    print("Request.form keys:", list(request.form.keys()))

    file = request.files.get('video')
    print("Filename received:", file.filename if file else "No file found")

    # Validate file
    if not file or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file format"}), 400

    try:
        # Save uploaded video
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Check cache
        if filename in analysis_cache:
            return jsonify(analysis_cache[filename])

        # Step 1: Gemini response on raw video
        video_data = input_video_setup(filepath, file.mimetype)
        raw_response = get_gemini_response(input_prompt, video_data, "")
        data = clean_and_parse_response(raw_response)

        # Step 2: Override reps with MediaPipe rep count
        rep_count, duration = analyze_with_mediapipe(filepath)
        data["repetitions"] = rep_count

        # Step 3 (Optional): Re-call Gemini for updated context (optional if needed)
        # You can skip this call if not needed.
        raw_response = get_gemini_response(input_prompt, video_data, "")
        data = clean_and_parse_response(raw_response)

        # Cache result and return
        analysis_cache[filename] = data
        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/')
def health_check():
    return jsonify({"status": "Workout Analysis API is running"}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
