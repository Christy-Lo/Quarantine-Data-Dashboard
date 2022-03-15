from django.shortcuts import render
from django.http import HttpResponse
import json

import subprocess
def install(name):
    subprocess.call(['pip', 'install', name])
install('requests')


import requests
from datetime import *

def getapi(dataset, date):
    occupancy_query = {
            "resource": "http://www.chp.gov.hk/files/misc/occupancy_of_quarantine_centres_eng.csv",
            "section": 1,
            "format": "json",
            "filters": [[1, "eq", [date]]],
            "sorts": [[8, "desc"]] # sorted by unit available
            }
    confines_query = {
            "resource": "http://www.chp.gov.hk/files/misc/no_of_confines_by_types_in_quarantine_centres_eng.csv",
            "section": 1,
            "format": "json",
            "filters": [[1, "eq", [date]]]
            }
    if dataset == "occupancy":
        url = "https://api.data.gov.hk/v2/filter?q=" + json.dumps(occupancy_query)        
    elif dataset == "confines":
        url = "https://api.data.gov.hk/v2/filter?q=" + json.dumps(confines_query)
    
    response = requests.get(url)
    if response.ok:
        return response.json()
    return None

def getdf():
    df = {}
    df["has_data"] = False
    df["connected"] = False
    
    listofdate=[]
    yesterday = date.today() - timedelta(days=1)
    for i in range(7):
        next_date = yesterday - timedelta(days=i)
        listofdate.append(next_date.strftime("%d/%m/%Y"))

    for showdate in listofdate:
        if (getapi("occupancy", showdate) is None) or (getapi("confines", showdate) is None):
            continue        # skip this day
        else: 
            df["connected"] = True
            occupancy_data = getapi("occupancy", showdate)
            confines_data = getapi("confines", showdate)
            
        try:
            units_in_use = 0
            units_available = 0
            persons_quarantined = 0
            for centre in occupancy_data:
                units_in_use = units_in_use + centre["Current unit in use"]
                units_available = units_available + centre["Ready to be used (unit)"]
                persons_quarantined = persons_quarantined + centre["Current person in use"]

            # check count_consistent
            confines_data = confines_data[0]  # get the dictionary from the list
            count_consistent = False
            if (confines_data["Current number of close contacts of confirmed cases"] + confines_data["Current number of non-close contacts"] == persons_quarantined):
                count_consistent = True

            centre_list=[]
            for centre in occupancy_data[:3]: # data from api are sorted
                centre_list.append (
                    {"name": centre["Quarantine centres"],
                    "units":centre["Ready to be used (unit)"]}
                )

            df["has_data"] = True
            df["data"] = {
                "date": showdate,
                "units_in_use": units_in_use,
                "units_available": units_available,
                "persons_quarantined": persons_quarantined,
                "non_close_contacts": confines_data["Current number of non-close contacts"],
                "count_consistent": count_consistent,
            }
            df["centres"] = centre_list

        except:
            continue  # skip this day

        return df

def dashboard(request):
    df = getdf()
    return render(request, "templates/dashboard3.html", df)
