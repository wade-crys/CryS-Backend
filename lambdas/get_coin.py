import json
from SPARQLWrapper import SPARQLWrapper, JSON


def lambda_handler(event, context):
    sparql = SPARQLWrapper(
        "http://ec2-3-120-140-142.eu-central-1.compute.amazonaws.com:7200//repositories/crys")
    query_base = """
PREFIX crys: <http://example.com/crys#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#> 
SELECT * WHERE {{
    ?coin rdf:type crys:Coin ;
          crys:id "{id}"^^xsd:nonNegativeInteger ;
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
    optional {{?coin  crys:announcement ?announcement}} .
    optional {{?coin  crys:chat ?chat }} .
    optional {{?coin  crys:explorer ?explorer }} .
    optional {{?coin  crys:message_board ?message_board }} .
    optional {{?coin  crys:reddit ?reddit }} .
    optional {{?coin  crys:source_code ?source_code }} .
    optional {{?coin  crys:technical_doc ?technical_doc }} .
    optional {{?coin  crys:twitter ?twitter }} .
    optional {{?coin  crys:website ?website }} .
    optional {{?coin  crys:platform ?platform }} .
    optional {{?coin  rdfs:seeAlso ?seeAlso }} .
}}
"""


    path_params = event["pathParameters"]

    id = path_params['id']
    query = query_base.format(id=id)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    if len(results['results']['bindings']):
        return {
            'statusCode': 200,
            'body': json.dumps(results)
        }
    return {
        'statusCode': 404,
        'body': 'No coin for given id'
    }


# Local test bench
r = lambda_handler({"pathParameters":{"id":"1"}}, None)
results = json.loads(r['body'])['results']['bindings']
for result in results:
    print(result['symbol']['value'], result['name']['value'])

