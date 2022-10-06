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

    countriesQuery = graphene.List(
        CountryDetail,
        first=graphene.Int(),
        skip=graphene.Int(),
        )

    countryQuery= graphene.Field(CountryDetail,common_name=graphene.String())

    countriesByLanguageQuery = graphene.List(
        CountryDetail,
        language = graphene.String()
        )

    def resolve_countriesQuery(parent, info, first=None, skip=None):
        qs = list(CountryDetailsModel.objects.all())
        if skip:
                qs = qs[skip:]

        if first:
            qs = qs[:first]
        return qs

    def resolve_countryQuery(parent,info, common_name):
        return CountryDetailsModel.objects.get(common_name=common_name)

    def resolve_countriesByLanguageQuery(parent, info, language):
        return CountryDetailsModel.objects.filter(languages__contains=language)


schema = graphene.Schema(query=Query, auto_camelcase=False)

# result = schema.execute(
#     '''
#     {
#         countriesQuery(first: 0, skip: 0){
#             _id
#             common_name
#             official_name
#             capital
#             languages
#             region
#             subregion
#             latlng
#             population
#             un_member
#             area
#         }
#     }
#     '''
# )

# print(result.errors)
# items = dict(result.data.items())
# print(json.dumps(items, indent=4))
# print()

# result = schema.execute(
#     '''
#     {
#         countryQuery (common_name:"Malta"){
#             _id
#             common_name
#             official_name
#             capital
#             languages
#             region
#             subregion
#             latlng
#             population
#             un_member
#             area
#         }
#     }
#     '''
# )

result = schema.execute(
    '''
    {
        countriesByLanguageQuery (language:"Spanish"){
            common_name
        }
    }
    '''
)

# print(result)
items = dict(result.data.items())
print(json.dumps(items, indent=4))