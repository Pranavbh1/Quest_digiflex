import os
import json
from google.generativeai import configure, GenerativeModel
from datetime import datetime
import pytz


# Load Gemini
configure(api_key=os.getenv("GEMINI_API_KEY"))
model = GenerativeModel("gemini-1.5-flash")


def generate_plan_with_gemini(user_query, user_context):
    india = pytz.timezone("Asia/Kolkata")
    today = datetime.now(india).strftime("%Y-%m-%d")
    prompt = f"""
You are a personal fitness assistant. The user has the following profile and progress history. Based on their query, generate a detailed workout and fitness plan ONLY IF ASKED.

User Query:
{user_query}

User Data:
{json.dumps(user_context, indent=2)}

Instructions:
- Generate a daily plan ONLY IF ASKED and use timestamp and datetime and if user ask to generate then Progress history as of {today}.
- Include exercises (name, sets, reps, weights), water intake, estimated calories, and step goals.
- Spread the response across 7 days unless the query specifies a different number and always keep randomness while regenrating plan again and again.

Be clear, concise, and motivating. And most important thing dont ask any extra information just reply on user data what you have fetched from json file. 
"""
    response = model.generate_content(prompt)
    return response.text
