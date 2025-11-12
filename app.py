from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import requests
from datetime import datetime

app = Flask(__name__)

# ✅ Database setup (SQLite file)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ✅ Define the Weather model (table)
class Weather(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100), nullable=False)
    temperature = db.Column(db.Float)
    description = db.Column(db.String(100))
    time = db.Column(db.String(50))

# ✅ Create all tables
with app.app_context():
    db.create_all()

# ✅ Main route
@app.route('/', methods=['GET', 'POST'])
def index():
    weather = None
    error = None

    if request.method == 'POST':
        city = request.form['city'].strip()

        try:
            # Get lat/lon for city (using geocoding API)
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
            geo_response = requests.get(geo_url).json()

            if "results" not in geo_response:
                error = "City not found!"
            else:
                lat = geo_response["results"][0]["latitude"]
                lon = geo_response["results"][0]["longitude"]
                country = geo_response["results"][0]["country"]

                # Get weather data
                weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=Asia/Kolkata"
                weather_response = requests.get(weather_url).json()

                data = weather_response.get("current_weather", {})
                if data:
                    weather = {
                        "city": city.title(),
                        "country": country,
                        "temperature": data["temperature"],
                        "windspeed": data["windspeed"],
                        "description": f"Code {data['weathercode']}",
                        "time": data["time"]
                    }

                    # ✅ Save to database
                    entry = Weather(
                        city=weather["city"],
                        temperature=weather["temperature"],
                        description=weather["description"],
                        time=weather["time"]
                    )
                    db.session.add(entry)
                    db.session.commit()
                else:
                    error = "Weather data unavailable."
        except Exception as e:
            error = f"Error fetching data: {e}"

    # ✅ Fetch last 5 records for display
    history = Weather.query.order_by(Weather.id.desc()).limit(5).all()

    return render_template('index.html', weather=weather, error=error, history=history)

# ✅ Clear search history
@app.route('/clear', methods=['POST'])
def clear_history():
    Weather.query.delete()
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
