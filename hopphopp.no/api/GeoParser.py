import requests
import json
import datetime

# Prepare variables.
geo_file = './json/geofile_' + datetime.datetime.today().strftime('%Y%m%d-%H%M%S') + '.json'
geo_data = []
tmp_name = ""
response = requests.get('http://partners.api.skyscanner.net/apiservices/geo/v1.0?apiKey=SECRET')
data = response.json()
# Parse all the JSON returned.
# Seperate continents, countries, cities and airports.
for continent in data['Continents']:
    curr_continent = continent['Name']
    for country in continent['Countries']:
        curr_country = country['Name']
        tmp_name = country['Name'] + ' ( ' + curr_continent + ' )'
        geo_data.append({
            "Id": country['Id'],
            "Name": tmp_name,
            "Type": "country"
        })
        for city in country['Cities']:
            curr_city = city['Name']
            tmp_name = city['Name'] + ' ( ' + curr_country + ' )'
            geo_data.append({
                "Id": city['Id'],
                "Name": tmp_name,
                "Type": "city"
            })
            for airport in city['Airports']:
                tmp_name = airport['Name'] + ' ( ' + airport['Id'] + ' )'
                geo_data.append({
                    "Id": airport['Id'],
                    "Name": tmp_name,
                    "Type": "airport"
                })
# write all data to the file used by HoppAPI.py 
with open(geo_file, 'w') as f:
    f.write(json.dumps(geo_data, indent=4, sort_keys=False))
f.closed
