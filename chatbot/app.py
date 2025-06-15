from flask import Flask, request, jsonify
from flask_session import Session
from routes.recommendation import recommendation_bp
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Register route blueprint
app.register_blueprint(recommendation_bp)

@app.route("/")
def health_check():
    return jsonify({"message": "API is running"}), 200

if __name__ == "__main__":
    app.run(debug=True)
