import json
from SPARQLWrapper import SPARQLWrapper, JSON


def lambda_handler(event, context):
    sparql = SPARQLWrapper(
        "http://ec2-3-120-140-142.eu-central-1.compute.amazonaws.com:7200//repositories/crys")
    query_base = """
PREFIX crys: <http://example.com/crys#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT ?price_history ?belongs_to ?value ?at_date WHERE {
    ?coin rdf:type crys:Coin ;
          crys:cmc_rank ?cmc_rank ;
          crys:symbol ?belongs_to .
    ?price_history rdf:type crys:PriceHistory ;
                   crys:belongs_to ?coin ;
                   crys:value ?value ;
                   crys:at_date ?at_date .
"""
    filter = '    filter (?belongs_to = "{}")'

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
    query += "} order by ?cmc_rank DESC(?at_date)"

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
print(lambda_handler({'queryStringParameters': {'limit': '2'}}, None))