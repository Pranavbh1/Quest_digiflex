from flask import Flask, render_template, request
from dotenv import load_dotenv
import os
import google.generativeai as genai
from PIL import Image
import json
from io import BytesIO
import base64

# Load .env
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB

# --- Gemini API Call ---
def get_gemini_response(input_text, image, prompt):
    model = genai.GenerativeModel('gemini-2.0-flash-lite', generation_config={'temperature': 0.02})
    response = model.generate_content([input_text, image[0], prompt])
    return response.text

# --- Clean JSON ---
def clean_and_parse_response(response_text):
    if response_text.startswith("```json"):
        response_text = response_text.replace("```json", "").replace("```", "").strip()
    elif response_text.startswith("```"):
        response_text = response_text.replace("```", "").strip()
    return json.loads(response_text)

# --- Convert Image ---
def format_image_for_gemini(pil_image):
    img_byte_arr = BytesIO()
    pil_image.save(img_byte_arr, format="PNG")
    img_data = img_byte_arr.getvalue()
    return [{"mime_type": "image/png", "data": img_data}]


input_prompt = """
You are a certified nutritionist. Given an image of food, analyze and return ONLY this JSON:

{
  "dish_name": "Name of the dish",
  "ingredients": [{"name": "ingredient", "quantity": "amount"}],
  "macronutrients": {
    "Calories": "100 kcal",
    "Protein": "10 g",
    "Carbohydrates": "20 g",
    "Fats": "5 g"
  },
  "micronutrients": {
    "Vitamin A": "100 IU",
    "Iron": "5 mg",
    "Calcium": "50 mg"
  },
  "improvements": {
    "suggestions": ["Replace sugar with honey", "Add more vegetables"]
  }
}

If you don't know the exact values, provide reasonable estimates. Output only JSON.And if photo other then food comes then you should reply that "Please Enter the Food Picture".
"""




@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")
@app.route('/analyze', methods=['POST'])
def analyze():
    uploaded_file = request.files.get('file')
    captured_image_data = request.form.get('captured_image')

    image = None

    if uploaded_file and uploaded_file.filename != '':
        image = Image.open(uploaded_file)

    elif captured_image_data:
        try:
            header, encoded = captured_image_data.split(",", 1)
            img_bytes = base64.b64decode(encoded)
            image = Image.open(BytesIO(img_bytes))
        except Exception as e:
            return f"❌ Error processing captured image: {e}", 400

    if image is None:
        return "❌ No image provided", 400

    try:
        image_data = format_image_for_gemini(image)
        # raw_response = get_gemini_response("", image_data, input_prompt)
        # data = clean_and_parse_response(raw_response)
        raw_response = get_gemini_response("", image_data, input_prompt)

        # Simple check: if response looks like JSON
        if raw_response.strip().startswith("{") or raw_response.strip().startswith("```json"):
            data = clean_and_parse_response(raw_response)
            return render_template("result.html", data=data)
        else:
            return render_template("result.html", data={"error": raw_response})


                # Check if Gemini said it's not a food image
        if (
            isinstance(data, dict) and 
            data.get("dish_name", "").lower() in ["unknown", "", "not food", "no food detected"]
            or not data.get("ingredients")  # if ingredients are empty or missing
        ):
            return render_template("result.html", data={"error": "❌ Please enter a valid food picture."})

        # Otherwise show the results
        return render_template("result.html", data=data)


        # return render_template("result.html", data=data)
    except Exception as e:
        return f"❌ Gemini error: {e}", 500


if __name__ == "__main__":
    # app.run(debug=True)       #uncomment it when in production
    app.run(host='0.0.0.0', port=5000, debug=True)     #for testing on other PC
