import graphene
from graphene_mongo import MongoengineObjectType
from models import CountryDetails as CountryDetailsModel
from mongoengine import connect
import json

connect(db="countries", host="localhost", port=27017)


class CountryDetail(MongoengineObjectType):
    class Meta:
        model = CountryDetailsModel
        # filter_fields = ['fisrt_name']

class Query(graphene.ObjectType):
    all_countries = graphene.List(CountryDetail)
    single_country= graphene.Field(CountryDetail,common_name=graphene.String())

    def resolve_all_countries(parent, info):
        return list(CountryDetailsModel.objects.all())

    def resolve_single_country(parent,info, common_name):
        return CountryDetailsModel.objects.get(common_name=common_name)

schema = graphene.Schema(query=Query, auto_camelcase=False)

result = schema.execute(
    '''
    {
        all_countries{
            _id
            common_name
            official_name
            capital
            languages
            region
            subregion
            latlng{
                coordinates
            }
            population
            un_member
            area
        }
    }
    '''
)

print(result.errors)
items = dict(result.data.items())
print(json.dumps(items, indent=4))
print()

result = schema.execute(
    '''
    {
        single_country (common_name:"Spain"){
            _id
            common_name
            official_name
            capital
            languages
            region
            subregion
            latlng{
                coordinates
            }
            population
            un_member
            area
        }
    }
    '''
)

# print(result.errors)
items = dict(result.data.items())
print(json.dumps(items, indent=4))