package Utils;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.flink.api.java.tuple.Tuple5;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.HashMap;
import java.util.Map;

public class JsonUtils {
    private static final Logger logger = LoggerFactory.getLogger(JsonUtils.class);
    private static final ObjectMapper objectMapper = new ObjectMapper();

    public static String convertToJson(Tuple5<String, Double, String, String, String> tuple) {
        if (tuple == null) {
            return "{}";
        }
        try {
            Map<String, Object> dataMap = new HashMap<>();
            dataMap.put("field0", tuple.f0);
            dataMap.put("field1", tuple.f1);
            dataMap.put("field2", tuple.f2);
            dataMap.put("field3", tuple.f3);
            dataMap.put("field4", tuple.f4);

            return objectMapper.writeValueAsString(dataMap);
        } catch (JsonProcessingException e) {
            logger.error("Error serializing tuple to JSON: {}", e.getMessage());
            return "{}";
        }
    }
}
