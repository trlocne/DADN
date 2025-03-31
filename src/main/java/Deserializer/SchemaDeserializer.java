package Deserializer;

import org.apache.avro.Schema;
import org.apache.avro.generic.GenericRecord;
import org.apache.avro.io.BinaryDecoder;
import org.apache.avro.io.DecoderFactory;
import org.apache.avro.specific.SpecificDatumReader;
import org.apache.avro.specific.SpecificRecordBase;
import org.apache.flink.api.common.serialization.DeserializationSchema;
import org.apache.flink.api.common.typeinfo.TypeInformation;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;

public abstract class SchemaDeserializer<T extends SpecificRecordBase> implements DeserializationSchema<T> {
    private final Class<T> targetType;
    private transient SpecificDatumReader<T> reader;
    private transient BinaryDecoder decoder;

    public SchemaDeserializer(Class<T> targetType) {
        this.targetType = targetType;
    }

    @Override
    public void open(InitializationContext context) throws Exception {
        Schema schema = getSchema();
        this.reader = new SpecificDatumReader<>(schema);
    }

    protected abstract Schema getSchema();

    protected GenericRecord deserializeGen(byte[] bytes) throws IOException {
        if (bytes == null || bytes.length == 0) {
            throw new IOException("Received empty byte array for deserialization");
        }

        byte[] messageContent = new byte[bytes.length - 5];
        System.arraycopy(bytes, 5, messageContent, 0, messageContent.length);

        InputStream inputStream = new ByteArrayInputStream(messageContent);
        decoder = DecoderFactory.get().binaryDecoder(inputStream, decoder);
        return reader.read(null, decoder);
    }

    @Override
    public abstract T deserialize(byte[] bytes) throws  IOException;

    @Override
    public boolean isEndOfStream(T t) {
        return false;
    }

    @Override
    abstract public TypeInformation<T> getProducedType();
}
