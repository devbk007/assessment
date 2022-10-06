import graphene
import falcon
import json

from graphene_mongo import MongoengineObjectType
from models import CountryDetails as CountryDetailsModel
from mongoengine import connect
from haversine import haversine
from bson import ObjectId

from contextlib import redirect_stdout
from os import devnull
from collections import OrderedDict


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

def set_graphql_allow_header(req, resp, resource):
    "Sets the 'Allow' header on responses to GraphQL requests."
    resp.set_header('Allow', 'GET, POST, OPTIONS')


# Define the GraphQL API endpoint
@falcon.after(set_graphql_allow_header)
class GraphQLResource:
    "Main GraphQL server. Integrates with the predefined Graphene schema."
    def on_options(self, req, resp):
        "Handles OPTIONS requests."
        resp.status = falcon.HTTP_204
        pass

    def on_head(self, req, resp):
        "Handles HEAD requests. No content."
        pass

    def on_get(self, req, resp):
        if req.params and 'query' in req.params and req.params['query']:
            query = str(req.params['query'])
        else:
            # this means that there aren't any query params in the url
            resp.status = falcon.HTTP_400
            resp.body = json.dumps(
                {"errors": [{"message": "Must provide query string."}]},
                separators=(',', ':')
            )
            return

        if 'variables' in req.params and req.params['variables']:
            try:
                variables = json.loads(str(req.params['variables']),
                                       object_pairs_hook=OrderedDict)
            except json.decoder.JSONDecodeError:
                resp.status = falcon.HTTP_400
                resp.body = json.dumps(
                    {"errors": [{"message": "Variables are invalid JSON."}]},
                    separators=(',', ':')
                )
                return
        else:
            variables = ""

        if 'operationName' in req.params and req.params['operationName']:
            operation_name = str(req.params['operationName'])
        else:
            operation_name = None

        # redirect stdout of schema.execute to /dev/null
        with open(devnull, 'w') as f:
            with redirect_stdout(f):
                # run the query
                if operation_name is None:
                    result = schema.execute(query, variable_values=variables)
                else:
                    result = schema.execute(query, variable_values=variables,
                                            operation_name=operation_name)

        # construct the response and return the result
        if result.data:
            data_ret = {'data': result.data}
            resp.status = falcon.HTTP_200
            resp.body = json.dumps(data_ret, separators=(',', ':'))
            return
        elif result.errors:
            # NOTE: these errors don't include the optional 'locations' key
            err_msgs = [{'message': str(i)} for i in result.errors]
            resp.status = falcon.HTTP_400
            resp.body = json.dumps({'errors': err_msgs}, separators=(',', ':'))
            return
        else:
            # responses should always have either data or errors
            raise

    def on_post(self, req, resp):
        # parse url parameters in the request first
        if req.params and 'query' in req.params and req.params['query']:
            query = str(req.params['query'])
        else:
            query = None

        if 'variables' in req.params and req.params['variables']:
            try:
                variables = json.loads(str(req.params['variables']),
                                       object_pairs_hook=OrderedDict)
            except json.decoder.JSONDecodeError:
                resp.status = falcon.HTTP_400
                resp.body = json.dumps(
                    {"errors": [{"message": "Variables are invalid JSON."}]},
                    separators=(',', ':')
                )
                return
        else:
            variables = None

        if 'operationName' in req.params and req.params['operationName']:
            operation_name = str(req.params['operationName'])
        else:
            operation_name = None

        # Next, handle 'content-type: application/json' requests
        if req.content_type and 'application/json' in req.content_type:
            # error for requests with no content
            if req.content_length in (None, 0):
                resp.status = falcon.HTTP_400
                resp.body = json.dumps(
                    {"errors": [{"message": "POST body sent invalid JSON."}]},
                    separators=(',', ':')
                )
                return

            # read and decode request body
            raw_json = req.stream.read()
            try:
                req.context['post_data'] = json.loads(
                                               raw_json.decode('utf-8'),
                                               object_pairs_hook=OrderedDict
                                           )
            except json.decoder.JSONDecodeError:
                resp.status = falcon.HTTP_400
                resp.body = json.dumps(
                    {"errors": [{"message": "POST body sent invalid JSON."}]},
                    separators=(',', ':')
                )
                return

            # build the query string (Graph Query Language string)
            if (query is None and req.context['post_data'] and
                    'query' in req.context['post_data']):
                query = str(req.context['post_data']['query'])
            elif query is None:
                resp.status = falcon.HTTP_400
                resp.body = json.dumps(
                    {"errors": [{"message": "Must provide query string."}]},
                    separators=(',', ':')
                )
                return

            # build the variables string (JSON string of key/value pairs)
            if (variables is None and req.context['post_data'] and
                    'variables' in req.context['post_data'] and
                    req.context['post_data']['variables']):
                variables = str(req.context['post_data']['variables'])
                try:
                    json_str = str(req.context['post_data']['variables'])
                    variables = json.loads(json_str,
                                           object_pairs_hook=OrderedDict)
                except json.decoder.JSONDecodeError:
                    resp.status = falcon.HTTP_400
                    resp.body = json.dumps(
                        {"errors": [
                            {"message": "Variables are invalid JSON."}
                        ]},
                        separators=(',', ':')
                    )
                    return
            elif variables is None:
                variables = ""

            # build the operationName string (matches a query or mutation name)
            if (operation_name is None and
                    'operationName' in req.context['post_data'] and
                    req.context['post_data']['operationName']):
                operation_name = str(req.context['post_data']['operationName'])

        # Alternately, handle 'content-type: application/graphql' requests
        elif req.content_type and 'application/graphql' in req.content_type:
            # read and decode request body
            req.context['post_data'] = req.stream.read().decode('utf-8')

            # build the query string
            if query is None and req.context['post_data']:
                query = str(req.context['post_data'])

            elif query is None:
                resp.status = falcon.HTTP_400
                resp.body = json.dumps(
                    {"errors": [{"message": "Must provide query string."}]},
                    separators=(',', ':')
                )
                return

        # Skip application/x-www-form-urlencoded since they are automatically
        # included by setting req_options.auto_parse_form_urlencoded = True

        elif query is None:
            # this means that the content-type is wrong and there aren't any
            # query params in the url
            resp.status = falcon.HTTP_400
            resp.body = json.dumps(
                {"errors": [{"message": "Must provide query string."}]},
                separators=(',', ':')
            )
            return

        # redirect stdout of schema.execute to /dev/null
        with open(devnull, 'w') as f:
            with redirect_stdout(f):
                # run the query
                if operation_name is None:
                    result = schema.execute(query, variable_values=variables)
                else:
                    result = schema.execute(query, variable_values=variables,
                                            operation_name=operation_name)

        # construct the response and return the result
        if result.data:
            data_ret = {'data': result.data}
            resp.status = falcon.HTTP_200
            resp.body = json.dumps(data_ret, separators=(',', ':'))
            return
        elif result.errors:
            # NOTE: these errors don't include the optional 'locations' key
            err_msgs = [{'message': str(i)} for i in result.errors]
            resp.status = falcon.HTTP_400
            resp.body = json.dumps({'errors': err_msgs}, separators=(',', ':'))
            return
        else:
            # responses should always have either data or errors
            raise

    def on_put(self, req, resp):
        "Handles PUT requests."
        resp.status = falcon.HTTP_405
        resp.body = json.dumps(
            {"errors": [
                {"message": "GraphQL only supports GET and POST requests."}
            ]},
            separators=(',', ':')
        )

    def on_patch(self, req, resp):
        "Handles PATCH requests."
        resp.status = falcon.HTTP_405
        resp.body = json.dumps(
            {"errors": [
                {"message": "GraphQL only supports GET and POST requests."}
            ]},
            separators=(',', ':')
        )

    def on_delete(self, req, resp):
        "Handles DELETE requests."
        resp.status = falcon.HTTP_405
        resp.body = json.dumps(
            {"errors": [
                {"message": "GraphQL only supports GET and POST requests."}
            ]},
            separators=(',', ':')
        )


# Load the API object
graphQL_api = falcon.API()

# Keep query parameters even when they have no corresponding values (aka flags)
graphQL_api.req_options.keep_blank_qs_values = True

# Automatically parse a www-form-urlencoded POST body & insert into req.params
graphQL_api.req_options.auto_parse_form_urlencoded = True

# Connect routes to resources
graphQL_route = GraphQLResource()

# Attach main routes to API
graphQL_api.add_route('/graphql', graphQL_route)