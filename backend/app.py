from flask import Flask
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import os
from datetime import datetime
import pandas as pd
import calendar
from bson import json_util

app = Flask(__name__)
load_dotenv(dotenv_path="../os.env")
mongo_url = os.getenv('MONGO_URI')
app.config["MONGO_URI"] = mongo_url
mongo = PyMongo(app)
fda_nda = mongo.cx.fda.novel_drugs_approvals


@app.route('/')
def default():
    return 'testing'

# api to fetch data from database
@app.route('/api/data', methods=['GET'])
def get_full_data():
    df = get_data()
    most_recent_drug = list(fda_nda.find().sort({'_id': -1}).limit(1))
    return json_util.dumps({'data': df.to_dict(),
                            'most_recent_drug': most_recent_drug})


# helper function to fetch data from database and perform transformation
def get_data():
    data = list(fda_nda.find())
    df = pd.DataFrame(data)
    df['Year'] = df['Approval Date'].dt.year  # Extract the year
    return df


# api to fetch latest data in the current month
@app.route('/api/update', methods=['GET'])
def update():
    start_date = datetime(datetime.today().year, datetime.today().month, 1)

    # Get the end date as the last second of the current month
    _, last_day = calendar.monthrange(start_date.year, start_date.month)
    end_date = datetime(start_date.year, start_date.month, last_day, 23, 59, 59)

    record = list(fda_nda.find({
        "Approval Date": {
            "$gte": start_date,
            "$lte": end_date
        }
    }))

    most_recent_drug = list(fda_nda.find().sort({'_id': -1}).limit(1))
    df = pd.DataFrame(record)
    df['Year'] = df['Approval Date'].dt.year

    most_recent_drug = list(fda_nda.find().sort({'_id': -1}).limit(1))
    return json_util.dumps({'data': df.to_dict(),
                            "most_recent_drug": most_recent_drug
                            })


if __name__ == "__main__":
    app.run(debug=True)
