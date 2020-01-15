import java.io.*;

import com.amazonaws.services.lambda.runtime.RequestStreamHandler;
import com.amazonaws.services.lambda.runtime.Context;
import org.apache.jena.query.ResultSet;
import org.apache.jena.rdf.model.Model;
import org.apache.jena.sparql.resultset.RDFOutput;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;


public class GetCoinLambdaHandler implements RequestStreamHandler{

    private JSONObject getResponse(String statusCode, String body){
        JSONObject responseJson = new JSONObject();
        responseJson.put("statusCode", statusCode);
        responseJson.put("body", body);
        return responseJson;
    }

    public String getCoin(String id, String format) {
        final StringBuilder response = new StringBuilder();
        String query = "" +
                "PREFIX crys: <http://example.com/crys#>\n" +
                "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n" +
                "PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> \n" +
                "\n" +
                "SELECT * WHERE {\n" +
                "    ?coin rdf:type crys:Coin ;\n" +
                "          crys:id \"%s\"^^xsd:nonNegativeInteger ;\n" +
                "          crys:cmc_rank ?cmc_rank ;\n" +
                "          crys:name ?name ;\n" +
                "          crys:synopsis ?description ;\n" +
                "          crys:symbol ?symbol ;\n" +
                "          crys:circulating_supply ?circulating_supply ;\n" +
                "          crys:date_added ?date_added ;\n" +
                "          crys:logo ?logo ;\n" +
                "          crys:market_cap ?market_cap ;\n" +
                "          crys:percent_change_24h ?percent_change_24h ;\n" +
                "          crys:percent_change_7d ?percent_change_7d ;\n" +
                "          crys:price ?price ;\n" +
                "          crys:status ?status ;\n" +
                "          crys:mineable ?mineable ;\n" +
                "    optional {?coin  crys:announcement ?announcement} .\n" +
                "    optional {?coin  crys:chat ?chat } .\n" +
                "    optional {?coin  crys:explorer ?explorer } .\n" +
                "    optional {?coin  crys:message_board ?message_board } .\n" +
                "    optional {?coin  crys:reddit ?reddit } .\n" +
                "    optional {?coin  crys:source_code ?source_code } .\n" +
                "    optional {?coin  crys:technical_doc ?technical_doc } .\n" +
                "    optional {?coin  crys:twitter ?twitter } .\n" +
                "    optional {?coin  crys:website ?website } .\n" +
                "    optional {?coin  crys:platform ?platform } .\n" +
                "}";

        query = String.format(query, id);

        FusekiClient.executeQuery(query, qExec -> {
            ResultSet rs = qExec.execSelect();
            if (rs.hasNext()){
                Model model = RDFOutput.encodeAsModel(rs);
                StringWriter out = new StringWriter();
                model.write(out, format);
                response.append(out.toString());
            } else {
                response.append("404");
            }
        });

        return response.toString();
    }

    public void handleRequest(InputStream inputStream, OutputStream outputStream, Context context) throws IOException {
        // call these or really weird shit happens
        org.apache.jena.query.ARQ.init();
        org.apache.jena.riot.RIOT.init();
        // allowed query string parameters
        String id = null;
        String format = "TURTLE";

        String statusCode = "200";
        String body = null;

        BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream));
        JSONParser parser = new JSONParser();
        JSONObject event = null;

        try {
            event = (JSONObject)parser.parse(reader);
            System.out.println(event.toString());
            if (event.get("pathParameters") != null)
            {
                JSONObject qps = (JSONObject)event.get("pathParameters");
                if ( qps.get("id") != null) {
                    id = qps.get("id").toString();

                }
            }
            if (event.get("queryStringParameters") != null)
            {
                JSONObject qps = (JSONObject)event.get("queryStringParameters");
                if ( qps.get("format") != null) {
                    format = (String)qps.get("format");
                }
            }
        }
        catch(Exception pex) {
            statusCode = "400";
            body = pex.toString();
            pex.printStackTrace();
        }

        if (body == null)
            body = getCoin(id, format);
        if (body.equals("404")){
            body = "No coin with specified id";
            statusCode = "404";
        }
        JSONObject response = getResponse(statusCode, body);

        OutputStreamWriter writer = new OutputStreamWriter(outputStream, "UTF-8");
        writer.write(response.toString());
        writer.close();
    }

    public static void main(String[] args) throws IOException {
        GetCoinLambdaHandler handler = new GetCoinLambdaHandler();
        InputStream is = new FileInputStream("test_get_coin.json");
        OutputStream os = new FileOutputStream("file.json");
        handler.handleRequest(is, os, null);
    }

}
