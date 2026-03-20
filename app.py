from flask import Flask, render_template, request, jsonify
import os
import requests
from werkzeug.utils import secure_filename
from text_model import analyze_text
from image_model import analyze_image
from database import init_db, insert_alert, get_all_alerts

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize DB (with migrations if needed)
init_db()

ALERT_COLORS = {
    'tsunami': 'RED',
    'cyclone': 'ORANGE',
    'storm': 'YELLOW',
    'flood': 'BLUE',
    'high waves': 'ORANGE',
    'oil spill': 'YELLOW',
    'default': 'GRAY'
}

def get_severity_label(score):
    if score >= 0.8: return "CRITICAL"
    elif score >= 0.6: return "HIGH"
    elif score >= 0.3: return "MEDIUM"
    else: return "LOW"

def geocode_location(location_name):
    """ Fetch coordinates for a location string using OpenStreetMap Nominatim. """
    if not location_name: return None, None
    try:
        # User-Agent is required by Nominatim
        headers = {'User-Agent': 'OceanHazardSystem_App'}
        response = requests.get(f"https://nominatim.openstreetmap.org/search?q={location_name}&format=json&limit=1", headers=headers, timeout=5)
        data = response.json()
        if data and len(data) > 0:
            return data[0]['lat'], data[0]['lon']
    except Exception as e:
        print(f"Geocoding Error: {e}")
    return None, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    text_content = request.form.get('text_content', '')
    image = request.files.get('image')
    
    image_path = ""
    if image and image.filename != '':
        filename = secure_filename(image.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(path)
        image_path = path
        
    text_results = analyze_text(text_content)
    
    image_results = {'detected_indicators': [], 'probability': 0.0, 'explanation': "No image provided."}
    if image_path:
        image_results = analyze_image(image_path)
        
    detected_hazards = text_results['detected_hazards']
    is_real = text_results['is_real']
    
    hazard_types = set(detected_hazards)
    mapping = {'stormy sea': 'storm', 'flood': 'flood', 'large waves': 'high waves', 'damaged boats': 'cyclone'}
    for ind in image_results['detected_indicators']:
        mapped_hazard = mapping.get(ind)
        if mapped_hazard:
            hazard_types.add(mapped_hazard)
            
    hazard_types = list(hazard_types)
    is_hazard_detected = len(hazard_types) > 0
    
    alert_triggered = False
    primary_hazard = "Unknown"
    
    # Hazard Severity Prediction Equation
    if image_path:
        severity_score = (text_results['confidence'] * 0.4) + (image_results['probability'] * 0.6)
    else:
        # If no image, base entirely off text
        severity_score = text_results['confidence'] * 0.6  # Penalize slightly for missing payload
    
    severity_level = get_severity_label(severity_score)
    location_name = text_results.get('location', 'Unknown Region')
    
    if is_hazard_detected and is_real:
        alert_triggered = True
        
        if "tsunami" in hazard_types: primary_hazard = "tsunami"
        elif "cyclone" in hazard_types: primary_hazard = "cyclone"
        elif "storm" in hazard_types: primary_hazard = "storm"
        elif "flood" in hazard_types: primary_hazard = "flood"
        elif hazard_types: primary_hazard = hazard_types[0]
            
        lat, lng = geocode_location(location_name)
        insert_alert(text_content, image_path, primary_hazard, "Real", severity_score, location_name, lat, lng, severity_level)
    
    color = ALERT_COLORS.get(primary_hazard, 'GRAY') if alert_triggered else 'GREEN'
    
    # Constructing XAI Output Reason Text
    explanation = text_results['explanation'].copy()
    if image_path:
        explanation.append(image_results['explanation'])
    
    return render_template('result.html', 
                           alert_triggered=alert_triggered,
                           primary_hazard=primary_hazard.upper(),
                           confidence=round(severity_score, 2),
                           severity=severity_level,
                           color=color,
                           text_results=text_results,
                           image_results=image_results,
                           explanation=explanation,
                           location=location_name)

@app.route('/dashboard')
def dashboard():
    alerts = get_all_alerts()
    return render_template('dashboard.html', alerts=alerts)

@app.route('/map')
def map_dashboard():
    return render_template('map_dashboard.html')

@app.route('/api/alerts')
def fetch_alerts():
    # JSON endpoint for real-time polling
    alerts = get_all_alerts()
    return jsonify({'alerts': alerts})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
