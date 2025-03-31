package Deserializer;

import com.yolohome.DoorDevice;
import org.apache.avro.Schema;
import org.apache.avro.generic.GenericRecord;
import org.apache.flink.api.common.typeinfo.TypeInformation;

import java.io.IOException;

public class DoorDeviceDeserializer extends SchemaDeserializer<DoorDevice> {
    public DoorDeviceDeserializer() {
        super(DoorDevice.class);
    }

    @Override
    protected Schema getSchema() {
        return DoorDevice.getClassSchema();
    }

    @Override
    public DoorDevice deserialize(byte[] bytes) throws IOException {
        GenericRecord record = deserializeGen(bytes);
        return DoorDevice.newBuilder()
                .setIdDoor(record.get("id_door") != null ? record.get("id_door").toString() : null)
                .setBbcServo(record.get("bbc_servo") != null ? record.get("bbc_servo").toString() : null)
                .setBbcName(record.get("bbc_name") != null ? record.get("bbc_name").toString() : null)
                .setBbcPassword(record.get("bbc_password") != null ? record.get("bbc_password").toString() : null)
                .setTimestamp(record.get("timestamp") != null ? record.get("timestamp").toString() : null)
                .build();
    }

    @Override
    public TypeInformation<DoorDevice> getProducedType() {
        return TypeInformation.of(DoorDevice.class);
    }
}