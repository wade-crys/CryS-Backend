import org.apache.jena.query.QueryExecution;
import org.apache.jena.query.QueryExecutionFactory;

import java.util.function.Consumer;

public class FusekiClient {

    static void executeQuery(String query, Consumer<QueryExecution> body) {
        System.out.println(query);
        String fusekiEndpoint = "http://ec2-3-120-140-142.eu-central-1.compute.amazonaws.com:7201/crys/sparql";
        try (QueryExecution qExec = QueryExecutionFactory.sparqlService(fusekiEndpoint, query)) {
            body.accept(qExec);
        }
    }
}
