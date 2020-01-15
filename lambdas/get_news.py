import json
from SPARQLWrapper import SPARQLWrapper, JSON


def lambda_handler(event, context):
    sparql = SPARQLWrapper(
        "http://ec2-3-120-140-142.eu-central-1.compute.amazonaws.com:7200//repositories/crys")
    query_base = """
PREFIX crys: <http://example.com/crys#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT ?news ?title ?description ?source ?url ?create_date (group_concat(?symbol;separator=",") as ?about) WHERE {
    ?news rdf:type crys:News ;
          crys:title ?title ;
          crys:source ?source ;
          crys:url ?url ;
          crys:date_published ?create_date .
    ?news crys:description ?description .
    optional {
        ?news crys:about ?coin .
        ?coin crys:symbol ?symbol .
    } .
"""
    filter = '    filter (?symbol = "{}")'

    params = event["queryStringParameters"]
    if not params:
        params = dict()
    symbol = params.get('symbol', None)
    limit = params.get('limit', None)
    try:
        limit = int(limit)
    except (ValueError, TypeError):
        limit = None
    query = query_base
    if symbol:
        query += filter.format(symbol.upper()) + '\n'
    query += "} group by ?news ?title ?description ?source ?url ?create_date order by ?create_date"

    if limit:
        query += " limit {}".format(str(limit))
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    return {
        'statusCode': 200,
        'body': json.dumps(results)
    }


# Local test bench
print(lambda_handler({'queryStringParameters': {'limit': '10'}}, None))

