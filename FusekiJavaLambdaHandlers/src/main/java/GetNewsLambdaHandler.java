import java.io.*;

import com.amazonaws.services.lambda.runtime.RequestStreamHandler;
import com.amazonaws.services.lambda.runtime.Context;
import org.apache.jena.rdf.model.Model;
import org.apache.jena.sparql.resultset.RDFOutput;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;


public class GetNewsLambdaHandler implements RequestStreamHandler{

    private JSONObject getResponse(String statusCode, String body){
        JSONObject responseJson = new JSONObject();
        responseJson.put("statusCode", statusCode);
        responseJson.put("body", body);
        return responseJson;
    }

    public String getNews(Long limit, String symbol, String format) {
        final StringBuilder response = new StringBuilder();
        String query = "" +
                "PREFIX crys: <http://example.com/crys#>\n" +
                "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n" +
                "\n" +
                "SELECT ?news ?title ?description ?source ?url ?create_date (group_concat(?symbol;separator=\",\") as ?about) WHERE {\n" +
                "    ?news rdf:type crys:News ;\n" +
                "          crys:title ?title ;\n" +
                "          crys:source ?source ;\n" +
                "          crys:url ?url ;\n" +
                "          crys:date_published ?create_date .\n" +
                "    ?news crys:description ?description .\n" +
                "    optional {\n" +
                "        ?news crys:about ?coin .\n" +
                "        ?coin crys:symbol ?symbol .\n" +
                "    } .\n";
        String group_by = "} group by ?news ?title ?description ?source ?url ?create_date order by ?create_date ";

        if (symbol != null)
            query += "    filter (?symbol = \"" + symbol.toUpperCase() + "\")\n";
        query += group_by ;

        if (limit != null)
            query += "limit " + limit.toString();

        FusekiClient.executeQuery(query, qExec -> {
            Model model = RDFOutput.encodeAsModel(qExec.execSelect());
            StringWriter out = new StringWriter();
            model.write(out, format);
            response.append(out.toString());
        });

        return response.toString();
    }

    public void handleRequest(InputStream inputStream, OutputStream outputStream, Context context) throws IOException {
        // call these or really weird shit happens
        org.apache.jena.query.ARQ.init();
        org.apache.jena.riot.RIOT.init();
        // allowed query string parameters
        Long limit = null;
        String symbol = null;
        String format = "TURTLE";

        String statusCode = "200";
        String body = null;

        BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream));
        JSONParser parser = new JSONParser();
        JSONObject event = null;

        try {
            event = (JSONObject)parser.parse(reader);
            System.out.println(event.toString());
            if (event.get("queryStringParameters") != null)
            {
                JSONObject qps = (JSONObject)event.get("queryStringParameters");
                if ( qps.get("limit") != null) {
                    limit = Long.valueOf(qps.get("limit").toString());

                }
                if ( qps.get("symbol") != null) {
                    symbol = (String)qps.get("symbol");
                }
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
            body = getNews(limit, symbol, format);
        JSONObject response = getResponse(statusCode, body);

        OutputStreamWriter writer = new OutputStreamWriter(outputStream, "UTF-8");
        writer.write(response.toString());
        writer.close();
    }

    public static void main(String[] args) throws IOException {
        GetNewsLambdaHandler handler = new GetNewsLambdaHandler();
        InputStream is = new FileInputStream("test_get_news.json");
        OutputStream os = new FileOutputStream("file.json");
        handler.handleRequest(is, os, null);
    }

}
