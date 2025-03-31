package Deserializer;

import com.yolohome.HumidityDevice;
import org.apache.avro.Schema;
import org.apache.avro.generic.GenericRecord;
import org.apache.flink.api.common.typeinfo.TypeInformation;

import java.io.IOException;

public class HumidityDeviceDeserializer extends SchemaDeserializer<HumidityDevice> {
    public HumidityDeviceDeserializer() {
        super(HumidityDevice.class);
    }

    @Override
    protected Schema getSchema() {
        return HumidityDevice.getClassSchema();
    }

    @Override
    public HumidityDevice deserialize(byte[] bytes) throws IOException {
        GenericRecord record = deserializeGen(bytes);
        return HumidityDevice.newBuilder()
                .setIdHum(record.get("id_hum") != null ? record.get("id_hum").toString() : null)
                .setBbcHum(record.get("bbc_hum") != null ? (Float) record.get("bbc_hum") : null)
                .setBbcName(record.get("bbc_name") != null ? record.get("bbc_name").toString() : null)
                .setBbcPassword(record.get("bbc_password") != null ? record.get("bbc_password").toString() : null)
                .setTimestamp(record.get("timestamp") != null ? record.get("timestamp").toString() : null)
                .build();
    }

    @Override
    public TypeInformation<HumidityDevice> getProducedType() {
        return TypeInformation.of( HumidityDevice.class);
    }
}