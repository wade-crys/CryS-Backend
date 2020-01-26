import json
from SPARQLWrapper import SPARQLWrapper, JSON


def lambda_handler(event, context):
    sparql = SPARQLWrapper(
        "http://ec2-3-120-140-142.eu-central-1.compute.amazonaws.com:7200//repositories/crys")
    query_base = """
PREFIX crys: <http://example.com/crys#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#> 
SELECT * WHERE {
    ?coin rdf:type crys:Coin ;
          crys:id ?id ;
          crys:cmc_rank ?cmc_rank ;
          crys:name ?name ;
          crys:synopsis ?description ;
          crys:symbol ?symbol ;
          crys:circulating_supply ?circulating_supply ;
          crys:date_added ?date_added ;
          crys:logo ?logo ;
          crys:market_cap ?market_cap ;
          crys:percent_change_24h ?percent_change_24h ;
          crys:percent_change_7d ?percent_change_7d ;
          crys:price ?price ;
          crys:status ?status ;
          crys:mineable ?mineable ;
    optional {?coin  crys:announcement ?announcement} .
    optional {?coin  crys:chat ?chat } .
    optional {?coin  crys:explorer ?explorer } .
    optional {?coin  crys:message_board ?message_board } .
    optional {?coin  crys:reddit ?reddit } .
    optional {?coin  crys:source_code ?source_code } .
    optional {?coin  crys:technical_doc ?technical_doc } .
    optional {?coin  crys:twitter ?twitter } .
    optional {?coin  crys:website ?website } .
    optional {?coin  crys:platform ?platform } .
    optional {?coin  rdfs:seeAlso ?seeAlso } .
"""

    filter = '    FILTER (regex(?name, "{search_string}", "i") || regex(?symbol, "{search_string}", "i")) '

    params = event["queryStringParameters"]
    if not params:
        params = dict()
    search_string = params.get('query', None)
    limit = params.get('limit', None)
    try:
        limit = int(limit)
    except (ValueError, TypeError):
        limit = None
    query = query_base
    if search_string:
        query += filter.format(search_string=search_string) + '\n'
    query += "} order by ?cmc_rank"
    if limit:
        query += " limit {}".format(str(limit))


    sparql.setQuery(query)
    sparql.method = 'POST'
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    return {
        'statusCode': 200,
        'body': json.dumps(results)
    }

# Local test bench
r = lambda_handler({'queryStringParameters': {'query': 'dog', 'limit': 10}}, None)
results = json.loads(r['body'])['results']['bindings']
for result in results:
    print(result['symbol']['value'], result['name']['value'])

