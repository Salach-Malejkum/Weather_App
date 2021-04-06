import sqlite3
import os
import sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for, flash
import sys
import requests


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
db = SQLAlchemy(app)
app.secret_key = '9yU;`4xUr@kj$CCp'


class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=True, nullable=False)

    def __repr__(self):
        return "%r" % self.name


con = sqlite3.connect('weather.db')
cursor = con.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
if not cursor.fetchall() or not os.path.exists('weather.db'):
    db.create_all()


def get_weather(name):
    api = "ffaf9c72af3d62a288a0dc3abcb1d271"

    # Send get request to openweathermap website with city name and our api
    r = requests.get(f"http://api.openweathermap.org/data/2.5/weather?q={name}&appid={api}")

    if r.status_code == 200:
        # Get temperature and weather state data from our request
        current_temp = int(r.json()["main"]["temp"] - 273)
        weather_state = r.json()["weather"][0]["main"]
        return current_temp, weather_state
    return None, None


@app.route('/', methods=['POST'])
def add_city():
    # Check what caused post request
    if 'city_name' in request.form:
        # Get city name from POST request
        city_name = request.form['city_name']
        current_temp, weather_state = get_weather(city_name)

        # If name of city is correct
        if current_temp is not None and weather_state is not None:
            # If city is not in database add it database and redirect to homepage
            city = City(name=city_name)
            try:
                db.session.add(city)
                db.session.commit()
            # If city is already in database show message
            except (sqlite3.IntegrityError, sqlalchemy.exc.IntegrityError):
                flash('The city has already been added to the list!')
        # If name of city is incorrect
        else:
            flash('The city doesn\'t exist!')
    elif 'id' in request.form:
        # Delete chosen city
        city = City.query.filter_by(name=request.form['id']).first()
        db.session.delete(city)
        db.session.commit()

    return redirect(url_for('main_page'))


@app.route('/', methods=['GET'])
def main_page():
    list_weather_info = []
    # Add cities from database to list and put them to html
    for city in City.query.all():
        current_temp, weather_state = get_weather(city.name)
        list_weather_info.append({"degrees": current_temp, "state": weather_state, "city": city.name})
    return render_template("index.html", weather=list_weather_info)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()
