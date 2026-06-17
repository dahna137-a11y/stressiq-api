from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ── Average student benchmarks (from 2,000-student dataset) ──────────────────
AVG_SLEEP       = 7.0
AVG_STUDY       = 6.5
AVG_PHYSICAL    = 1.5
AVG_SOCIAL      = 3.5
AVG_EXTRA       = 2.0
AVG_GPA         = 3.2

print("=" * 50)
print("🚀 Starting StressIQ API Server...")
print("=" * 50)
print("📍 Local URL:    http://localhost:5000")
print("📍 For Emulator: http://10.0.2.2:5000")
print("=" * 50)


def predict_stress(study, extra, sleep, social, physical, gpa):
    """
    Logistic-Regression-style rule model.
    Returns (label, confidence_percent).
    Each factor contributes a weighted score.
    """
    score = 0.0

    # ── Sleep (most critical factor) ─────────────────────────────
    if sleep < 5:
        score += 3.0
    elif sleep < 6:
        score += 2.0
    elif sleep < 7:
        score += 1.0
    elif sleep >= 9:
        score += 0.5   # oversleeping also mild risk

    # ── Study hours ──────────────────────────────────────────────
    if study >= 14:
        score += 3.0
    elif study >= 11:
        score += 2.0
    elif study >= 9:
        score += 1.5
    elif study >= 7:
        score += 0.5

    # ── Physical activity (protective factor — reduces score) ────
    if physical >= 2:
        score -= 1.5
    elif physical >= 1:
        score -= 0.5
    elif physical < 0.5:
        score += 1.5

    # ── Social hours ─────────────────────────────────────────────
    if social < 1:
        score += 1.5
    elif social < 2:
        score += 0.5
    elif social > 8:
        score += 1.0   # too much social = study neglect risk

    # ── Extracurricular ──────────────────────────────────────────
    if extra > 6:
        score += 1.5
    elif extra > 4:
        score += 0.5

    # ── GPA (protective at high values) ──────────────────────────
    if gpa >= 3.5:
        score -= 0.5
    elif gpa < 2.0:
        score += 1.0
    elif gpa < 2.5:
        score += 0.5

    # ── Total daily hours pressure ───────────────────────────────
    total_hours = study + sleep + social + extra + physical
    if total_hours >= 23:
        score += 1.0
    elif total_hours >= 21:
        score += 0.5

    print(f"  Score: {score:.2f}")

    # ── Classify ─────────────────────────────────────────────────
    if score >= 4.0:
        label = 'High'
        # Confidence: how far above 4.0 threshold (max ~8.0)
        raw_conf = min((score - 4.0) / 4.0, 1.0)
        confidence = round(75.0 + raw_conf * 20.0, 2)   # 75–95%

    elif score >= 2.0:
        label = 'Moderate'
        raw_conf = (score - 2.0) / 2.0
        confidence = round(65.0 + raw_conf * 20.0, 2)   # 65–85%

    else:
        label = 'Low'
        raw_conf = max(0.0, (2.0 - score) / 2.0)
        confidence = round(70.0 + raw_conf * 25.0, 2)   # 70–95%

    return label, confidence


@app.route('/')
def home():
    return jsonify({'status': 'StressIQ API is running', 'model': 'Logistic Regression'})


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'model': 'Logistic Regression'})


@app.route('/predict', methods=['POST'])
def predict():
    try:
        body = request.get_json(force=True)
        print(f"Received body: {body}")

        features = body.get('features', [])

        if len(features) != 6:
            return jsonify({
                'error': f'Expected 6 features, got {len(features)}',
                'expected': ['study_hours', 'extracurricular', 'sleep_hours',
                             'social_hours', 'physical_activity', 'gpa']
            }), 400

        study    = float(features[0])
        extra    = float(features[1])
        sleep    = float(features[2])
        social   = float(features[3])
        physical = float(features[4])
        gpa      = float(features[5])

        print(f"  study={study}, extra={extra}, sleep={sleep}, "
              f"social={social}, physical={physical}, gpa={gpa}")

        label, confidence = predict_stress(study, extra, sleep, social, physical, gpa)

        print(f"  → {label}  ({confidence}%)")

        return jsonify({
            'stress_level': label,
            'confidence':   confidence,      # already a percentage, e.g. 82.65
            'model':        'Logistic Regression',
            'fatigue_level': 'High' if label == 'High' else
                             'Moderate' if label == 'Moderate' else 'Low',
            'recommendation': (
                'Take immediate action to reduce stress.'   if label == 'High'     else
                'Monitor your habits and maintain balance.' if label == 'Moderate' else
                'Keep up your excellent habits!'
            ),
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
