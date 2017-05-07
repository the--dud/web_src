from flask import Flask, request, jsonify
import requests
import json
from copy import copy, deepcopy
from flask_restful import Api, Resource, reqparse


application = Flask(__name__)
api = Api(application)

# Variables
geofile_URI = './json/geofile_no.json'


# Helper Function: Takes IATA code and returns city name.
def get_city_name(iatacode): # Seaches geofile_URI for exact match on IATA code.
    tmp_city = ""
    with open(geofile_URI) as data_file:
        data_geo = json.load(data_file)
    for item in data_geo:
        if iatacode == item['Id']:
            return tmp_city
        if item['Type'] == "city":
            tmp_city = item['Name']
    return False

class searchGeo(Resource): # Searches geofile_URI for matches.
    def get(self, search_string):
        matches = []
        lsearch_string = search_string.lower()
        with open(geofile_URI) as data_file:
            data_geo = json.load(data_file)
        for item in data_geo:
            lid = item['Id'].lower()
            lname = item['Name'].lower()
            if lsearch_string in lid or lsearch_string in lname:
                matches.append(item)
        return matches

class getFlights(Resource): # Returns matching flight data from specific loc to specific loc on specific dates.
    def post(self):
        # POST data structure:
        ## {
        ## "from_IATA": IATA Code
        ## "to_IATA": IATA Code
        ## "out_date": YYYY-MM|YYYY-MM-DD
        ## "in_date": YYYY-MM|YYYY-MM-DD
        ## }

        # Define JSON structures
        data_goo = {
            "request": {
                "passengers": {
                    "adultCount": "1"
                },
                "slice": [{
                    "origin": "",
                    "destination": "",
                    "date": "",
                    "maxConnectionDuration": "240",
                    "maxStops": "1"
                },
                {
                    "origin": "",
                    "destination": "",
                    "date": "",
                    "maxConnectionDuration": "240",
                    "maxStops": "1"
                }],
                "solutions": "10"
            }
        }
        rs_data = {
            "carriers": [],
            "trips": []
        }
        rs_item = {
            "to": {
                "route": "",
                "num_stops": "",
                "duration": ""
            },
            "from": {
                "route": "",
                "num_stops": "",
                "duration": ""
            },
            "price": ""
        }
        rs_carrier = {
            "name": "",
            "code": ""
        }

        rd = request.get_json(force=True)
        data_goo['request']['slice'][0]['origin'] = rd['from_IATA']
        data_goo['request']['slice'][0]['destination'] = rd['to_IATA']
        data_goo['request']['slice'][0]['date'] = rd['out_date']
        data_goo['request']['slice'][1]['origin'] = rd['to_IATA']
        data_goo['request']['slice'][1]['destination'] = rd['from_IATA']
        data_goo['request']['slice'][1]['date'] = rd['in_date']


        # Get data (live flights) from Google QPX (data_goo [contains slice])
        response_goo = requests.post(
            'https://www.googleapis.com/qpxExpress/v1/trips/search?key=SECRET', json=data_goo)
        data_rgoo = response_goo.json()

        # Process data
        for car in data_rgoo['trips']['data']['carrier']:
            rs_carrier = copy(car)
            del (rs_carrier['kind'])
            rs_data['carriers'].append(copy(rs_carrier))

        for trip in data_rgoo['trips']['tripOption']:
            rs_item['price'] = trip['saleTotal']
            # slice[0] is from home to location
            rs_item['to']['num_stops'] = len(trip['slice'][0]['segment'])
            rs_item['to']['duration'] = trip['slice'][0]['duration']
            # slice[1] is return flight
            rs_item['from']['num_stops'] = len(trip['slice'][1]['segment'])
            rs_item['from']['duration'] = trip['slice'][1]['duration']
            tmp_route = ""
            for segment in trip['slice'][0]['segment']:
                if tmp_route == "":
                    tmp_route = segment['leg'][0]['origin'] + ":" + segment['leg'][0]['destination']
                else:
                    tmp_route = tmp_route + ":" +  segment['leg'][0]['destination']
                tmp_route = tmp_route + "-" + segment['flight']['carrier'] + segment['flight']['number']
            rs_item['to']['route'] = tmp_route
            tmp_route = ""
            for segment in trip['slice'][1]['segment']:
                if tmp_route == "":
                    tmp_route = segment['leg'][0]['origin'] + ":" + segment['leg'][0]['destination']
                else:
                    tmp_route = tmp_route + ":" +  segment['leg'][0]['destination']
                tmp_route = tmp_route + "-" + segment['flight']['carrier'] + segment['flight']['number']
            rs_item['from']['route'] = tmp_route
            #print(rs_item)
            rs_data['trips'].append(deepcopy(rs_item))

        return jsonify(rs_data)

class getRoutes(Resource): # Returns matching flight data from specific loc to ANYWHERE OR specific loc on date range.
    def post(self):
        # POST data structure:
        ## {
        ## "mode": simple|full
        ## "from_IATA": IATA Code
        ## "to_IATA": IATA Code OR Anywhere
        ## "date": YYYY-MM-DD
        ## "max_price": int
        ## }

        # Create return data structure
        rs_data = {
            "trips": []
        }
        rs_item = {
            "dest": "",
            "dest_IATA": "",
            "dest_city": "",
            "dest_country": "",
            "price": ""
        }
        # Get data (cached quotes) from Skyscanner
        rd = request.get_json(force=True)
        url = 'http://partners.api.skyscanner.net/apiservices/browsequotes/v1.0/NO/NOK/nb-NO/' + \
            rd['from_IATA'] + '/' + rd['to_IATA'] + '/' + rd['date'] + '/' + \
            rd['date'] + '/' + '?apiKey=SECRET'
        response_sky = requests.get(url)
        data_sky = response_sky.json()
        # Process data (cached quotes) from Skyscanner
        for q in data_sky['Quotes']:
            if ('OutboundLeg' in q):
                #print(q['OutboundLeg']['DestinationId'])
                for p in data_sky['Places']:
                    if (q['OutboundLeg']['DestinationId'] == p['PlaceId']):
                        rs_item['dest'] = p['Name']
                        rs_item['dest_IATA'] = p['IataCode']
                        rs_item['dest_city'] = p['CityName']
                        rs_item['dest_country'] = p['CountryName']
                        if (rs_item['dest_country'] == "De forente stater"):
                            rs_item['dest_country'] = "USA"
                        if (rs_item['dest_country'] == "De forente arabiske emirater"):
                            rs_item['dest_country'] = "UAE"
                        rs_item['price'] = int(q['MinPrice'])
            if (rs_item['price'] < rd['max_price']):
                rs_data['trips'].append(copy(rs_item))
                if (len(rs_data['trips']) > 1):
                    if (rs_data['trips'][-2]['dest'] == rs_data['trips'][-1]['dest']):
                        if (rs_data['trips'][-2]['price'] > rs_data['trips'][-1]['price']):
                            del rs_data['trips'][-2]
                        else:
                            del rs_data['trips'][-1]

        rs_data['trips'] = sorted(rs_data['trips'], key=lambda k: k['price'])
        return jsonify(rs_data)


class getDates(Resource): # Returns matching dates from specific loc to specific loc for specific month.
    def post(self):
        # POST data structure:
        ## {
        ## "from_IATA": IATA Code
        ## "to_IATA": IATA Code
        ## "date": YYYY-MM
        ## }

        # Create return data structure
        rs_data = {
            "dates": [],
            "min_price": 9999999,
            "max_price": 0
        }
        rs_item = {
            "direction": "",
            "date": "",
            "price": ""
        }
        # Get data (cached quotes) from Skyscanner
        rd = request.get_json(force=True)
        url = 'http://partners.api.skyscanner.net/apiservices/browsedates/v1.0/NO/NOK/nb-NO/' + \
            rd['from_IATA'] + '/' + rd['to_IATA'] + '/' + rd['date'] + '/' + \
            rd['date'] + '/' + '?apiKey=SECRET'
        response_sky = requests.get(url)
        data_sky = response_sky.json()

        # Process data (cached quotes) from Skyscanner
        for q in data_sky['Dates']['OutboundDates']:
            rs_item['direction'] = "out"
            rs_item['date'] = q['PartialDate']
            rs_item['price'] = q['Price']
            #print(rs_item['price'])
            if (rs_item['price'] < rs_data['min_price']):
                rs_data['min_price'] = copy(rs_item['price'])
            if (rs_item['price'] > rs_data['max_price']):
                rs_data['max_price'] = copy(rs_item['price'])
            rs_data['dates'].append(copy(rs_item))
        for q in data_sky['Dates']['InboundDates']:
            rs_item['direction'] = "in"
            rs_item['date'] = q['PartialDate']
            rs_item['price'] = q['Price']
            rs_data['dates'].append(copy(rs_item))
        return jsonify(rs_data)


# Setup the Api resource routing
api.add_resource(getFlights, '/api/flights')
api.add_resource(getRoutes, '/api/routes')
api.add_resource(getDates, '/api/dates')
api.add_resource(searchGeo, '/api/geo/<search_string>')

# Main class
if __name__ == "__main__":
    application.run(host='0.0.0.0', port=8080)
