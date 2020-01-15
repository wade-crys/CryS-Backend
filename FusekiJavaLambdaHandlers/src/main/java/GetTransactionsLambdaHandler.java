import java.io.*;

import com.amazonaws.services.lambda.runtime.RequestStreamHandler;
import com.amazonaws.services.lambda.runtime.Context;
import org.apache.jena.rdf.model.Model;
import org.apache.jena.sparql.resultset.RDFOutput;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;


public class GetTransactionsLambdaHandler implements RequestStreamHandler{

    private JSONObject getResponse(String statusCode, String body){
        JSONObject responseJson = new JSONObject();
        responseJson.put("statusCode", statusCode);
        responseJson.put("body", body);
        return responseJson;
    }

    public String getTransactions(Long limit, String symbol, String format) {
        final StringBuilder response = new StringBuilder();
        String query = "" +
                "PREFIX crys: <http://example.com/crys#>\n" +
                "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n" +
                "SELECT ?hash ?sender ?receiver ?amount ?amount_usd ?symbol ?date_traded WHERE {\n" +
                "    ?transaction rdf:type crys:Transaction ;\n" +
                "                 crys:hash ?hash ;\n" +
                "                 crys:sender ?sender ;\n" +
                "                 crys:receiver ?receiver ;\n" +
                "                 crys:amount ?amount ;\n" +
                "                 crys:amount_usd ?amount_usd ;\n" +
                "                 crys:transfers ?coin ;\n" +
                "                 crys:date_traded ?date_traded .\n" +
                "    ?coin crys:symbol ?symbol .           \n";

        if (symbol != null)
            query += "    filter (?symbol = \"" + symbol.toUpperCase() + "\")\n";

        query += "} order by DESC(?date_traded) ";

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
            body = getTransactions(limit, symbol, format);
        JSONObject response = getResponse(statusCode, body);

        OutputStreamWriter writer = new OutputStreamWriter(outputStream, "UTF-8");
        writer.write(response.toString());
        writer.close();
    }

    public static void main(String[] args) throws IOException {
        GetTransactionsLambdaHandler handler = new GetTransactionsLambdaHandler();
        InputStream is = new FileInputStream("test_get_transactions.json");
        OutputStream os = new FileOutputStream("file.json");
        handler.handleRequest(is, os, null);
    }

}
