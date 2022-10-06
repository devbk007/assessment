import graphene
import json

from graphene_mongo import MongoengineObjectType
from models import CountryDetails as CountryDetailsModel
from mongoengine import connect
from haversine import haversine
from bson import ObjectId

connect(db="countries", host="localhost", port=27017)

class CountryDetail(MongoengineObjectType):
    class Meta:
        model = CountryDetailsModel

class Query(graphene.ObjectType):

    countriesQuery = graphene.List(
        CountryDetail,
        first=graphene.Int(),
        skip=graphene.Int(),
        )

    countryQuery= graphene.Field(CountryDetail,id=graphene.String())

    countriesByLanguageQuery = graphene.List(
        CountryDetail,
        language = graphene.String()
        )

    countriesNearbyQuery = graphene.List(
        CountryDetail,
        latlng = graphene.List(graphene.Float, graphene.Float),
        distance = graphene.Float()
    )

    def resolve_countriesQuery(parent, info, first=None, skip=None):
        qs = list(CountryDetailsModel.objects.all())

        if skip:
                qs = qs[skip:]

        if first:
            qs = qs[:first]
        return qs

    def resolve_countryQuery(parent,info, id):
        try:
            return CountryDetailsModel.objects.get(_id=ObjectId(id))
        except Exception as e:
            print(e)


    def resolve_countriesByLanguageQuery(parent, info, language):
        return CountryDetailsModel.objects.filter(languages__contains=language)

    def resolve_countriesNearbyQuery(parent, info, latlng, distance):
        nearby_countries = []

        for e in CountryDetailsModel.objects.all():
            calculated_distance = haversine((e.latlng[0], e.latlng[1]), (latlng[0], latlng[1]))
            if calculated_distance <= distance:
                nearby_countries.append(e.common_name)

        return CountryDetailsModel.objects.filter(common_name__in=nearby_countries)

class countryEditMutation(graphene.Mutation):
    class Arguments:
        common_name = graphene.String()
        official_name = graphene.String()
        un_member = graphene.Boolean()
        population = graphene.Int()
        capital = graphene.String()
    
    country = graphene.Field(CountryDetail)

    def mutate(self, info, common_name, official_name, un_member, population, capital):
        country = CountryDetailsModel.objects.get(common_name=common_name)
        country.official_name = official_name
        country.un_member = un_member
        country.population = population
        country.capital = capital

        return countryEditMutation(country=country)

class Mutations(graphene.ObjectType):
    update_country = countryEditMutation.Field()

schema = graphene.Schema(query=Query, auto_camelcase=False, mutation=Mutations)