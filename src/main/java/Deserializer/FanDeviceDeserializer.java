package Deserializer;

import com.yolohome.FanDevice;
import org.apache.avro.Schema;
import org.apache.avro.generic.GenericRecord;
import org.apache.flink.api.common.typeinfo.TypeInformation;

import java.io.IOException;

public class FanDeviceDeserializer extends SchemaDeserializer<FanDevice> {
    public FanDeviceDeserializer() {
        super(FanDevice.class);
    }

    @Override
    protected Schema getSchema() {
        return FanDevice.getClassSchema();
    }

    @Override
    public FanDevice deserialize(byte[] bytes) throws IOException {
        GenericRecord record = deserializeGen(bytes);
        return FanDevice.newBuilder()
                .setIdFan(record.get("id_fan") != null ? record.get("id_fan").toString() : null)
                .setBbcFan(record.get("bbc_fan") != null ? record.get("bbc_fan").toString() : null)
                .setBbcControlFan(record.get("bbc_control_fan") != null ? record.get("bbc_control_fan").toString() : null)
                .setBbcName(record.get("bbc_name") != null ? record.get("bbc_name").toString() : null)
                .setBbcPassword(record.get("bbc_password") != null ? record.get("bbc_password").toString() : null)
                .setTimestamp(record.get("timestamp") != null ? record.get("timestamp").toString() : null)
                .build();
    }

    @Override
    public TypeInformation<FanDevice> getProducedType() {
        return TypeInformation.of(FanDevice.class);
    }
}
