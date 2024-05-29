from django.shortcuts import render
from django.http import HttpResponse
import json
import requests
from datetime import datetime, timedelta
import re


# Create your views here.

def getResponseOfCentres():
    
    global response_info, has_data, connected
    has_data = False
    connected = False
    
    prevDayCounter=0
    while (prevDayCounter <= 7):
        availableDate = datetime.date(datetime.now()) -timedelta(days=prevDayCounter)
    
        if (availableDate.month < 10):
            if (availableDate.day < 10):
                dateQueryFormat = "0"+str(availableDate.day)+"/0"+str(availableDate.month)+"/"+str(availableDate.year)
            else:
                dateQueryFormat = str(availableDate.day)+"/0"+str(availableDate.month)+"/"+str(availableDate.year)
        else:
            if (availableDate.day < 10):
                dateQueryFormat = "0"+str(availableDate.day)+"/"+str(availableDate.month)+"/"+str(availableDate.year)
            else:
                dateQueryFormat = str(availableDate.day)+"/"+str(availableDate.month)+"/"+str(availableDate.year)
        
        parameter = {"resource":"http://www.chp.gov.hk/files/misc/occupancy_of_quarantine_centres_eng.csv","section":1,"format":"json","filters":[[1,"eq",[dateQueryFormat]]]}
            
        parameter = json.dumps(parameter)
        response = requests.get("https://api.data.gov.hk/v2/filter?q="+parameter)
        response_info = json.loads(response.text)
        
        if (response.status_code == 200):
            connected = True
        
        if (len(response_info) != 0):
            has_data = True
            break
        prevDayCounter += 1
    
    if (prevDayCounter == 7):
        has_data = False
    
    return dateQueryFormat


def calculateUnitsInUse():
    
    totalDailyUnitsInUse = 0

    for record in response_info:
        totalDailyUnitsInUse += record['Current unit in use']
    
    return totalDailyUnitsInUse
    
    
def calculateUnitsAvailable():

    totalDailyUnitsAvailable= 0

    for record in response_info:
        totalDailyUnitsAvailable += record['Ready to be used (unit)']
    
    return totalDailyUnitsAvailable


def getResponseCentres(dateQueryFormat, listNo):
    
    parameter = {"resource":"http://www.chp.gov.hk/files/misc/occupancy_of_quarantine_centres_eng.csv","section":1,"format":"json","sorts":[[8,"desc"]],"filters":[[1,"eq",[dateQueryFormat]]]}

    parameter = json.dumps(parameter)
    response = requests.get("https://api.data.gov.hk/v2/filter?q="+parameter).text
    response_CentreInfo = json.loads(response)
    
    #print (response_CentreInfo)
    return response_CentreInfo[listNo]['Quarantine centres']


def getResponseCentreUnits(dateQueryFormat, listNo):
    
    parameter = {"resource":"http://www.chp.gov.hk/files/misc/occupancy_of_quarantine_centres_eng.csv","section":1,"format":"json","sorts":[[8,"desc"]],"filters":[[1,"eq",[dateQueryFormat]]]}

    parameter = json.dumps(parameter)
    response = requests.get("https://api.data.gov.hk/v2/filter?q="+parameter).text
    response_CentreUnitsInfo = json.loads(response)
    
    #print (response_CentreUnitsInfo)
    return response_CentreUnitsInfo[listNo]['Ready to be used (unit)']


def getResponseOfQuarantined(dateQueryFormat, infoRequest):

    global response_QuarantinedInfo

    parameter = {"resource":"http://www.chp.gov.hk/files/misc/no_of_confines_by_types_in_quarantine_centres_eng.csv","section":1,"format":"json","filters":[[1,"eq",[dateQueryFormat]]]}

    parameter = json.dumps(parameter)
    response = requests.get("https://api.data.gov.hk/v2/filter?q="+parameter).text
    response_QuarantinedInfo = json.loads(response)
    
    #print (response_QuarantinedInfo[0])
    return response_QuarantinedInfo[0][infoRequest]


def checkConsistency(dateQueryFormat):

    totalDailyCurrentPersonInUse = 0
    for record in response_info:
        totalDailyCurrentPersonInUse += record['Current person in use']
    
    if ( totalDailyCurrentPersonInUse == (getResponseOfQuarantined(dateQueryFormat, 'Current number of close contacts of confirmed cases') + getResponseOfQuarantined(dateQueryFormat, 'Current number of non-close contacts')) ):
        return True
    else:
        return False


def dataFeeder(request):
    
    dateQueryFormat = getResponseOfCentres()
    
    
    contextData = {"data":
                  { "date": dateQueryFormat, "units_in_use": calculateUnitsInUse(), "units_available": calculateUnitsAvailable(), "persons_quarantined":getResponseOfQuarantined(dateQueryFormat, 'Current number of close contacts of confirmed cases'), "non_close_contacts":getResponseOfQuarantined(dateQueryFormat, 'Current number of non-close contacts'), "count_consistent": checkConsistency(dateQueryFormat) },
                    "centres":
                    [
                    { "name":getResponseCentres(dateQueryFormat, 0), "units": getResponseCentreUnits(dateQueryFormat, 0) },
                    { "name":getResponseCentres(dateQueryFormat, 1), "units": getResponseCentreUnits(dateQueryFormat, 1) },
                    { "name":getResponseCentres(dateQueryFormat, 2), "units": getResponseCentreUnits(dateQueryFormat, 2) }
                    ],
                   "connected": connected, "has_data": has_data
                   }
                    
    return render(request, 'dashboard3.html', context=contextData)
