# Import dependencies
#%matplotlib inline
from matplotlib import style
style.use('fivethirtyeight')
import matplotlib.pyplot as plt

import numpy as np
import pandas as pd
import datetime as dt

# Reflect Tables into SQLAlchemy ORM
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, inspect

engine = create_engine("sqlite:///Resources/hawaii.sqlite", connect_args = {"check_same_thread": False})

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)
# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station
# Create our session (link) from Python to the DB
session = Session(engine)

# Import Flask
from flask import Flask, jsonify

#Flask Setup

app = Flask(__name__)

#Flask Routes

@app.route("/")
def home():
    return(
        f"welcome to the API queries!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start_date<br/>"
        f"/api/v1.0/start_date/end_date<br/>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    # Calculate the date 1 year ago from the last data point in the database
    last_date = session.query(func.max(Measurement.date)).first()[0]
    last_date_updated = dt.datetime.strptime(last_date,'%Y-%m-%d')
    year_ago = dt.date(year=last_date_updated.year-1, month=last_date_updated.month, day=last_date_updated.day)

    # Perform a query to retrieve the data and precipitation scores
    prcp_year_results = session.query(Measurement.date, Measurement.prcp).\
                        filter(Measurement.date >= year_ago).all()
    
    # Convert query resulst to dictionary
    prcp_data = {}
    for data in prcp_year_results:
        prcp_data[data[0]] = data[1]
        
    # Return resuls in Json
    return jsonify(prcp_data)

@app.route("/api/v1.0/stations")
def stations():
    # Query to return list of stations
    stations_list = session.query(Station.station, Station.name).all()
    
    # Convert query resulst to dictionary
    stations_data = {}
    for data in stations_list:
        stations_data[data[0]] = data[1]
    
    return jsonify(stations_data)


@app.route("/api/v1.0/tobs")
def tobs():
    # Query to obtain the most active station
    results = session.query(Measurement.station, func.count(Measurement.id)).\
        group_by(Measurement.station).order_by(func.count(Measurement.id).desc()).all()

    station_id = results[0][0]
    
    # Query the last 12 months tobs data for the station identified above
    last_date = session.query(func.max(Measurement.date)).first()[0]
    last_date_updated = dt.datetime.strptime(last_date,'%Y-%m-%d')
    year_ago = dt.date(year=last_date_updated.year-1, month=last_date_updated.month, day=last_date_updated.day)

    tobs_year_results = session.query(Measurement.station,Measurement.date, Measurement.tobs).\
                    filter(Measurement.station == station_id).\
                    filter(Measurement.date >= year_ago).all()
    
    # Convert query resulst to dictionary
    tobs_data = {}
    for data in tobs_year_results:
        tobs_data[data[1]] = data[2]
    
    msg = {"message": f"The most active station is {station_id} and following are 12 months temperature observed:"}
    return jsonify(msg, tobs_data)

                         
@app.route("/api/v1.0/<start_date>")
def temp_start(start_date):
    last_date = session.query(func.max(Measurement.date)).first()[0]
    
    if start_date > last_date:
        return(f"Please enter start date earlier than {last_date}")
    else:
        data = session.query(func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs)).\
                filter(Measurement.date >= start_date).all()
        min_temp = data[0][0]
        max_temp = data[0][1]
        avg_temp = data[0][2]
    
        temp_results = {"TMIN": min_temp, "TAVG": avg_temp, "TMAX": max_temp}
        
        msg = {"message":f"The minimum temperature, average temperature, and max temperature start from {start_date} are following:"}
        
        return jsonify(msg, temp_results)

@app.route("/api/v1.0/<start_date>/<end_date>")
def temp_range(start_date, end_date):
    last_date = session.query(func.max(Measurement.date)).first()[0]
    if start_date > end_date:
        return(f"Please enter start date earlier than end date.")
    elif start_date > last_date:
        return(f"Please enter start date earlier than {last_date}")
    else:
        data = session.query(func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs)).\
                filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).all()
        min_temp = data[0][0]
        max_temp = data[0][1]
        avg_temp = data[0][2]
    
        temp_results = {"TMIN": min_temp, "TAVG": avg_temp, "TMAX": max_temp}
        
        msg = {"message":f"The minimum temperature, average temperature, and max temperature for date range entered are as follow:"}
        
        return jsonify(msg, temp_results)


if __name__ == "__main__":
    app.run(debug=True)
