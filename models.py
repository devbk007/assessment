# Schema

from mongoengine import Document, StringField, IntField , BooleanField, PointField, DecimalField, DictField

class CountryDetails(Document):
    id = IntField()
    common_name = StringField(max_length=200)
    official_name = StringField(max_length=200)
    capital = StringField(max_length=200)
    languages = DictField()
    region = StringField(max_length=200)
    subregion = StringField(max_length=200)
    latlng = PointField()
    population = IntField()
    un_member = BooleanField()
    area = DecimalField()