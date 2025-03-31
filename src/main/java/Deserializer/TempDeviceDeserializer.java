package Deserializer;

import com.yolohome.TempDevice;
import org.apache.avro.Schema;
import org.apache.avro.generic.GenericRecord;
import org.apache.flink.api.common.typeinfo.TypeInformation;

import java.io.IOException;

public class TempDeviceDeserializer extends SchemaDeserializer<TempDevice> {
    public TempDeviceDeserializer() {
        super(TempDevice.class);
    }

    @Override
    protected Schema getSchema() {
        return TempDevice.getClassSchema();
    }

    @Override
    public TempDevice deserialize(byte[] bytes) throws IOException {
        GenericRecord record = deserializeGen(bytes);
        return TempDevice.newBuilder()
                .setIdTemp(record.get("id_temp") != null ? record.get("id_temp").toString() : null)
                .setBbcTemp(record.get("bbc_temp") != null ? (Float) record.get("bbc_temp") : null)
                .setBbcName(record.get("bbc_name") != null ? record.get("bbc_name").toString() : null)
                .setBbcPassword(record.get("bbc_password") != null ? record.get("bbc_password").toString() : null)
                .setTimestamp(record.get("timestamp") != null ? record.get("timestamp").toString() : null)
                .build();
    }

    @Override
    public TypeInformation<TempDevice> getProducedType() {
        return TypeInformation.of(TempDevice.class);
    }
}