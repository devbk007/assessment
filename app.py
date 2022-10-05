import requests

from mongoengine import connect
from models import CountryDetails

# Connecting to MongoDB
connect(db="countries", host="localhost", port=27017)

url="https://restcountries.com/v3.1/all"

z=requests.get(url)

data=z.json()

for i in data:
    try:
        country = CountryDetails(
            common_name = i["name"]["common"],
            official_name = i["name"]["official"],
            capital = i["capital"][0],
            languages = i["languages"],
            region = i["region"],
            subregion = i["subregion"],
            latlng = i["latlng"],
            population = i["population"],
            un_member = i["unMember"],
            area = i["area"]
        )
        country.save()

    except:
        continue

print("Successfully entered data in the database")