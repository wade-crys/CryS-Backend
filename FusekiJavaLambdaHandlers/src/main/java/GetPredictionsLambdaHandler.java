import java.io.*;

import com.amazonaws.services.lambda.runtime.RequestStreamHandler;
import com.amazonaws.services.lambda.runtime.Context;
import org.apache.jena.rdf.model.Model;
import org.apache.jena.sparql.resultset.RDFOutput;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;


public class GetPredictionsLambdaHandler implements RequestStreamHandler{

    private JSONObject getResponse(String statusCode, String body){
        JSONObject responseJson = new JSONObject();
        responseJson.put("statusCode", statusCode);
        responseJson.put("body", body);
        return responseJson;
    }

    public String getPredictions(Long period, String symbol, String format) {
        final StringBuilder response = new StringBuilder();
        String query = "" +
                "PREFIX crys: <http://example.com/crys#>\n" +
                "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n" +
                "\n" +
                "SELECT ?prediction ?symbol ?predicted_date ?predicted_price ?generated_at WHERE {\n" +
                "    ?prediction rdf:type crys:Prediction ;\n" +
                "                crys:for ?coin ;\n" +
                "                crys:predicted_date ?predicted_date ;\n" +
                "                crys:predicted_price ?predicted_price ;\n" +
                "                crys:generated_at ?generated_at .\n" +
                "    ?coin crys:symbol ?symbol\n";

        if (symbol != null)
            query += String.format("    filter (?symbol = \"%s\")\n ", symbol.toUpperCase());
        query += "} order by DESC(?generated_at) ?predicted_date ";
        if (period != null)
            query += "limit " + period.toString();

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
        Long period = null;
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
                if ( qps.get("period") != null) {
                    period = Long.valueOf(qps.get("period").toString());

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
            body = getPredictions(period, symbol, format);
        JSONObject response = getResponse(statusCode, body);

        OutputStreamWriter writer = new OutputStreamWriter(outputStream, "UTF-8");
        writer.write(response.toString());
        writer.close();
    }

    public static void main(String[] args) throws IOException {
        GetPredictionsLambdaHandler handler = new GetPredictionsLambdaHandler();
        InputStream is = new FileInputStream("test_get_predictions.json");
        OutputStream os = new FileOutputStream("file.json");
        handler.handleRequest(is, os, null);
    }

}
