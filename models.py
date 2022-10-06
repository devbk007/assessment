# Schema

from mongoengine import Document, StringField, IntField , BooleanField, DecimalField, ListField

class CountryDetails(Document):
    _id = StringField()
    common_name = StringField(max_length=200)
    official_name = StringField(max_length=200)
    capital = StringField(max_length=200)
    languages = ListField(StringField())
    region = StringField(max_length=200)
    subregion = StringField(max_length=200)
    latlng = ListField(DecimalField())
    population =  IntField()
    un_member = BooleanField()
    area = DecimalField()