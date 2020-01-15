import json
from SPARQLWrapper import SPARQLWrapper, JSON


def lambda_handler(event, context):
    sparql = SPARQLWrapper(
        "http://ec2-3-120-140-142.eu-central-1.compute.amazonaws.com:7200//repositories/crys")
    query_base = """
PREFIX crys: <http://example.com/crys#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT ?prediction ?symbol ?predicted_date ?predicted_price ?generated_at WHERE {
    ?prediction rdf:type crys:Prediction ;
                crys:for ?coin ;
                crys:predicted_date ?predicted_date ;
                crys:predicted_price ?predicted_price ;
                crys:generated_at ?generated_at .
    ?coin crys:symbol ?symbol
"""
    filter = '    filter (?symbol = "{}")'

    params = event["queryStringParameters"]
    if not params:
        params = dict()
    symbol = params.get('symbol', None)
    limit = params.get('period', None)
    try:
        limit = int(limit)
        if limit < 1 or limit > 7:
            return {
                'statusCode': 400,
                'body': 'Period must be between 1 and 7'
            }

    except (ValueError, TypeError):
        limit = None
    query = query_base
    if symbol:
        query += filter.format(symbol.upper()) + '\n'
    query += "} order by DESC(?generated_at) ?predicted_date"

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
print(lambda_handler({'queryStringParameters': {'period': '6', 'symbol': 'btc'}}, None))