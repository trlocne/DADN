package Deserializer;

import com.yolohome.LedDevice;
import org.apache.avro.Schema;
import org.apache.avro.generic.GenericRecord;
import org.apache.flink.api.common.typeinfo.TypeInformation;

import java.io.IOException;

public class LedDeviceDeserializer extends SchemaDeserializer<LedDevice> {
    public LedDeviceDeserializer() {
        super(LedDevice.class);
    }

    @Override
    protected Schema getSchema() {
        return LedDevice.getClassSchema();
    }

    @Override
    public LedDevice deserialize(byte[] bytes) throws IOException {
        GenericRecord record = deserializeGen(bytes);
        return LedDevice.newBuilder()
                .setIdLed(record.get("id_led") != null ? record.get("id_led").toString() : null)
                .setBbcLed(record.get("bbc_led") != null ? record.get("bbc_led").toString() : null)
                .setBbcName(record.get("bbc_name") != null ? record.get("bbc_name").toString() : null)
                .setBbcPassword(record.get("bbc_password") != null ? record.get("bbc_password").toString() : null)
                .setTimestamp(record.get("timestamp") != null ? record.get("timestamp").toString() : null)
                .build();
    }

    @Override
    public TypeInformation<LedDevice> getProducedType() {
        return TypeInformation.of(LedDevice.class);
    }
}
