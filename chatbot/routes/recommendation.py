from flask import Blueprint, request, jsonify
from utils.loader import get_user_context
from chat import generate_plan_with_gemini
import base64
import speech_recognition as sr
from io import BytesIO
import wave

recommendation_bp = Blueprint("recommendation", __name__)

@recommendation_bp.route("/api/generate_plan", methods=["POST"])
def generate_plan():
    context = get_user_context()
    query = "Generate a detailed exercise plan for the next 7 days starting from today based on your data."
    response = generate_plan_with_gemini(query, context)
    return jsonify({"response": response})

# @recommendation_bp.route("/api/query", methods=["POST"])
# def handle_query():
#     data = request.get_json()

#     query_text = data.get("query", "").strip()
#     query_audio = data.get("audio")  # Expecting base64 string (optional)

#     if query_audio and not query_text:
#         # If audio is provided but no text, decode (you can later add speech-to-text here)
#         query_text = "[Audio received, integrate speech-to-text if needed]"

#     if not query_text:
#         return jsonify({"error": "Query is required."}), 400

#     context = get_user_context()
#     response = generate_plan_with_gemini(query_text, context)
#     return jsonify({"response": response})

@recommendation_bp.route("/api/query", methods=["POST"])
def handle_query():
    data = request.get_json()

    query_text = data.get("query", "").strip()
    query_audio = data.get("audio")  # Expecting base64 string

    if query_audio and not query_text:
        try:
            # Decode the base64 audio string to bytes
            audio_bytes = base64.b64decode(query_audio)

            # Save the audio to an in-memory buffer
            audio_file = BytesIO(audio_bytes)

            # Ensure audio format is compatible with speech_recognition
            with wave.open(audio_file, 'rb') as wf:
                if wf.getsampwidth() != 2 or wf.getframerate() not in (16000, 44100):
                    return jsonify({"error": "Unsupported audio format. Use 16-bit PCM WAV at 16kHz or 44.1kHz."}), 400

            # Rewind the buffer and use recognizer
            audio_file.seek(0)
            recognizer = sr.Recognizer()                     # Transcribe audio
            with sr.AudioFile(audio_file) as source:
                audio = recognizer.record(source)
                query_text = recognizer.recognize_google(audio)

        except Exception as e:
            return jsonify({"error": f"Audio processing failed: {str(e)}"}), 400

    if not query_text:
        return jsonify({"error": "Query is required."}), 400

    context = get_user_context()
    response = generate_plan_with_gemini(query_text, context)
    return jsonify({"response": response})


# from flask import request
# import speech_recognition as sr

# @app.route('/api/query', methods=['POST'])
# def handle_query():
#     if 'audio' in request.files:
#         # Handle audio input
#         audio_file = request.files['audio']
#         recognizer = sr.Recognizer()
#         with sr.AudioFile(audio_file) as source:
#             audio = recognizer.record(source)
#             try:
#                 query = recognizer.recognize_google(audio)
#             except sr.UnknownValueError:
#                 return jsonify({"error": "Could not understand audio"}), 400
#             except sr.RequestError:
#                 return jsonify({"error": "Speech recognition failed"}), 500
#     else:
#         # Handle text input
#         data = request.get_json()
#         query = data.get('query', '')

#     # Generate response using query (text from speech or input)
#     response = generate_response(query)  # your custom logic
#     return jsonify({"response": response})
