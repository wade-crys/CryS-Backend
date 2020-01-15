import json
from SPARQLWrapper import SPARQLWrapper, JSON


def lambda_handler(event, context):
    sparql = SPARQLWrapper(
        "http://ec2-3-120-140-142.eu-central-1.compute.amazonaws.com:7200//repositories/crys")
    query_base = """
PREFIX crys: <http://example.com/crys#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT ?hash ?sender ?receiver ?amount ?amount_usd ?symbol ?date_traded WHERE {
    ?transaction rdf:type crys:Transaction ;
                 crys:hash ?hash ;
                 crys:sender ?sender ;
                 crys:receiver ?receiver ;
                 crys:amount ?amount ;
                 crys:amount_usd ?amount_usd ;
                 crys:transfers ?coin ;
                 crys:date_traded ?date_traded .
    ?coin crys:symbol ?symbol .           
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
    query += "} order by DESC(?date_traded) "

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
if __name__ == '__main__':
    print(lambda_handler({'queryStringParameters': {'limit': '2'}}, None))
