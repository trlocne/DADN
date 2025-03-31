package Flink;

import Deserializer.*;
import com.yolohome.*;
import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.common.functions.AggregateFunction;
import org.apache.flink.api.common.functions.MapFunction;
import org.apache.flink.api.common.functions.RichFilterFunction;
import org.apache.flink.api.common.state.ValueState;
import org.apache.flink.api.common.state.ValueStateDescriptor;
import org.apache.flink.api.java.tuple.Tuple5;
import org.apache.flink.api.java.tuple.Tuple6;
import org.apache.flink.configuration.Configuration;
import org.apache.flink.connector.elasticsearch.sink.Elasticsearch7SinkBuilder;
import org.apache.flink.connector.elasticsearch.sink.ElasticsearchSink;
import org.apache.flink.connector.jdbc.JdbcConnectionOptions;
import org.apache.flink.connector.jdbc.JdbcExecutionOptions;
import org.apache.flink.connector.jdbc.JdbcSink;
import org.apache.flink.connector.jdbc.JdbcStatementBuilder;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.streaming.api.windowing.assigners.SlidingProcessingTimeWindows;
import org.apache.flink.streaming.api.windowing.time.Time;
import org.apache.http.HttpHost;
import org.elasticsearch.action.index.IndexRequest;
import org.elasticsearch.client.Requests;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.sql.Timestamp;
import java.time.Duration;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

public class DataStreamYoloHome {
    private static final Logger LOG = LoggerFactory.getLogger(DataStreamYoloHome.class);
    private static final String jdbcUrl = "jdbc:postgresql://localhost:5432/postgres";
    private static final String username = "postgres";
    private static final String password = "postgres";

    private static boolean contentEquals(CharSequence a, CharSequence b) {
        if (a == null || b == null) return false;
        return !a.toString().equals(b.toString());
    }

    private static final DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss.SSSSSS");
    private static final DateTimeFormatter formatter1 = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    public static void main(String[] args) throws Exception {
        final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        env.enableCheckpointing(5000);

        KafkaSource<LedDevice> LedStream = KafkaSource.<LedDevice>builder()
                .setBootstrapServers("localhost:9092")
                .setTopics("led_schema")
                .setGroupId("led-group")
                .setStartingOffsets(OffsetsInitializer.latest())
                .setValueOnlyDeserializer(new LedDeviceDeserializer())
                .build();

        DataStream<LedDevice> LedData = env.fromSource(LedStream,
                        WatermarkStrategy.<LedDevice>forBoundedOutOfOrderness(Duration.ofSeconds(1))
                                .withTimestampAssigner((event, timestamp) -> {
                                    if (event.getTimestamp() == null) {
                                        LOG.warn("Event has null timestamp, using current time.");
                                        return System.currentTimeMillis();
                                    }
                                    LocalDateTime localDateTime = LocalDateTime.parse(event.getTimestamp().toString(), formatter);
                                    return Timestamp.valueOf(localDateTime).getTime();
                                }),
                        "LedEvents").returns(LedDevice.class)
                .filter(led -> led.getIdLed() != null)
                .keyBy(LedDevice::getIdLed)
                .filter(new RichFilterFunction<LedDevice>() {
                    private transient ValueState<LedDevice> lastState;

                    @Override
                    public boolean filter(LedDevice ledDevice) throws Exception {
                        LedDevice previous = lastState.value();
                        if (previous == null) {
                            lastState.update(ledDevice);
                            return true;
                        }
                        if (contentEquals(previous.getBbcLed(), ledDevice.getBbcLed())) {
                            lastState.update(ledDevice);
                            return true;
                        }
                        return false;
                    }

                    @Override
                    public void open(Configuration parameters) throws Exception {
                        ValueStateDescriptor<LedDevice> descriptor = new ValueStateDescriptor<>("lastStateLed", LedDevice.class);
                        lastState = getRuntimeContext().getState(descriptor);
                    }
                });

        KafkaSource<FanDevice> FanStream = KafkaSource.<FanDevice>builder()
                .setBootstrapServers("localhost:9092")
                .setTopics("fan_schema")
                .setGroupId("fan-group")
                .setStartingOffsets(OffsetsInitializer.latest())
                .setValueOnlyDeserializer(new FanDeviceDeserializer())
                .build();

        DataStream<FanDevice> FanData = env.fromSource(FanStream,
                        WatermarkStrategy.<FanDevice>forBoundedOutOfOrderness(Duration.ofSeconds(1))
                                .withTimestampAssigner((event, timestamp) -> {
                                    if (event.getTimestamp() == null) {
                                        LOG.warn("Event has null timestamp, using current time.");
                                        return System.currentTimeMillis();
                                    }
                                    LocalDateTime localDateTime = LocalDateTime.parse(event.getTimestamp().toString(), formatter);
                                    return Timestamp.valueOf(localDateTime).getTime();
                                }),
                        "FanEvents").returns(FanDevice.class)
                .filter(fan -> fan.getIdFan() != null)
                .filter(fan -> fan.getBbcControlFan() != null && Integer.parseInt(fan.getBbcControlFan().toString()) >= 0)
                .keyBy(FanDevice::getIdFan)
                .filter(new RichFilterFunction<FanDevice>() {
                    private transient ValueState<FanDevice> lastState;
                    private transient ValueState<Long> lastUpdateTime;

                    @Override
                    public void open(Configuration parameters) throws Exception {
                        ValueStateDescriptor<FanDevice> descriptor = new ValueStateDescriptor<>("lastStateFan", FanDevice.class);
                        ValueStateDescriptor<Long> timeDescriptor = new ValueStateDescriptor<>("lastUpdateTimeFan", Long.class);
                        lastState = getRuntimeContext().getState(descriptor);
                        lastUpdateTime = getRuntimeContext().getState(timeDescriptor);
                    }

                    @Override
                    public boolean filter(FanDevice fanDevice) throws Exception {
                        FanDevice previous = lastState.value();
                        Long lastUpdate = lastUpdateTime.value();
                        long currentTime = System.currentTimeMillis();

                        if (previous == null || lastUpdate == null) {
                            lastState.update(fanDevice);
                            lastUpdateTime.update(currentTime);
                            return true;
                        }

                        if (contentEquals(previous.getBbcFan(), fanDevice.getBbcFan()) ||
                                contentEquals(previous.getBbcControlFan(), fanDevice.getBbcControlFan())) {
                            lastState.update(fanDevice);
                            lastUpdateTime.update(currentTime);
                            return true;
                        }

                        return false;
                    }
                });

        KafkaSource<DoorDevice> DoorStream = KafkaSource.<DoorDevice>builder()
                .setBootstrapServers("localhost:9092")
                .setTopics("door_schema")
                .setGroupId("door-group")
                .setStartingOffsets(OffsetsInitializer.latest())
                .setValueOnlyDeserializer(new DoorDeviceDeserializer())
                .build();

        DataStream<DoorDevice> DoorData = env.fromSource(DoorStream,
                        WatermarkStrategy.<DoorDevice>forBoundedOutOfOrderness(Duration.ofSeconds(1))
                                .withTimestampAssigner((event, timestamp) -> {
                                    if (event.getTimestamp() == null) {
                                        LOG.warn("Event has null timestamp, using current time.");
                                        return System.currentTimeMillis();
                                    }
                                    LocalDateTime localDateTime = LocalDateTime.parse(event.getTimestamp().toString(), formatter);
                                    return Timestamp.valueOf(localDateTime).getTime();
                                }),
                        "DoorEvents").returns(DoorDevice.class)
                .filter(door -> door.getIdDoor() != null)
                .filter(door -> door.getBbcServo() != null)
                .keyBy(DoorDevice::getIdDoor)
                .filter(new RichFilterFunction<DoorDevice>() {
                    private transient ValueState<DoorDevice> lastState;
                    private transient ValueState<Long> lastUpdateTime;

                    @Override
                    public void open(Configuration parameters) throws Exception {
                        ValueStateDescriptor<DoorDevice> descriptor = new ValueStateDescriptor<>("lastStateDoor", DoorDevice.class);
                        ValueStateDescriptor<Long> timeDescriptor = new ValueStateDescriptor<>("lastUpdateTimeDoor", Long.class);
                        lastState = getRuntimeContext().getState(descriptor);
                        lastUpdateTime = getRuntimeContext().getState(timeDescriptor);
                    }

                    @Override
                    public boolean filter(DoorDevice doorDevice) throws Exception {
                        DoorDevice previous = lastState.value();
                        Long lastUpdate = lastUpdateTime.value();
                        long currentTime = System.currentTimeMillis();

                        if (previous == null || lastUpdate == null) {
                            lastState.update(doorDevice);
                            lastUpdateTime.update(currentTime);
                            return true;
                        }

                        if (contentEquals(previous.getBbcServo(), doorDevice.getBbcServo()) || contentEquals(previous.getBbcPassword(), doorDevice.getBbcPassword())) {
                            lastState.update(doorDevice);
                            return true;
                        }

                        return false;
                    }
                });

        KafkaSource<HumidityDevice> HumidityStream = KafkaSource.<HumidityDevice>builder()
                .setBootstrapServers("localhost:9092")
                .setTopics("hum_schema")
                .setGroupId("humidity-group")
                .setStartingOffsets(OffsetsInitializer.latest())
                .setValueOnlyDeserializer(new HumidityDeviceDeserializer())
                .build();

        DataStream<HumidityDevice> HumidityData = env.fromSource(HumidityStream,
                        WatermarkStrategy.<HumidityDevice>forBoundedOutOfOrderness(Duration.ofSeconds(1))
                                .withTimestampAssigner((event, timestamp) -> {
                                    if (event.getTimestamp() == null) {
                                        LOG.warn("Event has null timestamp, using current time.");
                                        return System.currentTimeMillis();
                                    }
                                    LocalDateTime localDateTime = LocalDateTime.parse(event.getTimestamp().toString(), formatter);
                                    return Timestamp.valueOf(localDateTime).getTime();
                                }), "HumidityEvents").returns(HumidityDevice.class)
                .filter(humidity -> humidity.getIdHum() != null)
                .filter(humidity -> humidity.getBbcHum() >= 0 && humidity.getBbcHum() <= 150);

        KafkaSource<TempDevice> TempStream = KafkaSource.<TempDevice>builder()
                .setBootstrapServers("localhost:9092")
                .setTopics("tem_schema")
                .setGroupId("temp-group")
                .setStartingOffsets(OffsetsInitializer.latest())
                .setValueOnlyDeserializer(new TempDeviceDeserializer())
                .build();

        DataStream<TempDevice> TempData = env.fromSource(TempStream,
                        WatermarkStrategy.<TempDevice>forBoundedOutOfOrderness(Duration.ofSeconds(1))
                                .withTimestampAssigner((event, timestamp) -> {
                                    if (event.getTimestamp() == null) {
                                        LOG.warn("Event has null timestamp, using current time.");
                                        return System.currentTimeMillis();
                                    }
                                    LocalDateTime localDateTime = LocalDateTime.parse(event.getTimestamp().toString(), formatter);
                                    return Timestamp.valueOf(localDateTime).getTime();
                                }),
                        "TempEvents").returns(TempDevice.class)
                .filter(temp -> temp.getIdTemp() != null)
                .filter(temp -> temp.getBbcTemp() >= 0 && temp.getBbcTemp() <= 150);

        LedData.print("LED Status: ");
        FanData.print("Fan Status: ");
        DoorData.print("Door Status: ");
        HumidityData.print("Humidity Level: ");
        TempData.print("Temperature: ");

        DataStream<Tuple5<String, Double, String, String, String>> avgTempStream = TempData
                .map(new MapFunctionTemp())
                .keyBy(t0 -> t0.f0)
                .window(SlidingProcessingTimeWindows.of(Time.minutes(2), Time.minutes(1)))
                .aggregate(new AverageAggregate());

        DataStream<Tuple5<String, Double, String, String, String>> avgHempStream = HumidityData
                .map(new MapFunctionHum())
                .keyBy(t0 -> t0.f0)
                .window(SlidingProcessingTimeWindows.of(Time.minutes(2), Time.minutes(1)))
                .aggregate(new AverageAggregate());

        avgTempStream.print("Avg Temperature: ");
        avgHempStream.print("Avg Hemp Level: ");

        JdbcExecutionOptions jobExecutionOptions = new JdbcExecutionOptions.Builder()
                .withBatchSize(1)
                .withBatchIntervalMs(0)
                .withMaxRetries(5)
                .build();

        JdbcConnectionOptions connectionOptions = new JdbcConnectionOptions.JdbcConnectionOptionsBuilder()
                .withUrl(jdbcUrl)
                .withDriverName("org.postgresql.Driver")
                .withUsername(username)
                .withPassword(password)
                .build();

        FanData.addSink(JdbcSink.sink(
                "INSERT INTO Fan (device_id, name, status, location, speed) VALUES (?, ?, ?, ?, ?) " +
                        "ON CONFLICT (device_id) " +
                        "DO UPDATE SET " +
                        "   name = COALESCE(EXCLUDED.name, Fan.name), " +
                        "   status = COALESCE(EXCLUDED.status, Fan.status), " +
                        "   location = COALESCE(EXCLUDED.location, Fan.location), " +
                        "   speed = COALESCE(EXCLUDED.speed, Fan.speed)",
                (JdbcStatementBuilder<FanDevice>) (ps, t) -> {
                    ps.setString(1, t.getIdFan() != null ? t.getIdFan().toString() : null);
                    ps.setString(2, null);
                    ps.setBoolean(3, t.getBbcFan() != null && !t.getBbcFan().toString().equals("0"));
                    ps.setString(4, null);
                    ps.setInt(5, t.getBbcControlFan() != null ? Integer.parseInt(t.getBbcControlFan().toString()) : 0);
                },
                jobExecutionOptions,
                connectionOptions
        ));

        FanData.addSink(JdbcSink.sink(
                "INSERT INTO Control (device_id, username, control_time) VALUES (?, ?, ?) " +
                        "ON CONFLICT (device_id, username, control_time) DO NOTHING",
                (JdbcStatementBuilder<FanDevice>) (ps, fanDevice) -> {
                    ps.setString(1, fanDevice.getIdFan() != null ? fanDevice.getIdFan().toString() : null);
                    ps.setString(2, fanDevice.getBbcName() != null ? fanDevice.getBbcName().toString() : null);
                    ps.setString(3, fanDevice.getTimestamp() != null ? fanDevice.getTimestamp().toString() : null);
                },
                jobExecutionOptions,
                connectionOptions
        ));

//        FanData.sinkTo(new Elasticsearch7SinkBuilder<FanDevice>()
//                .setHosts(new HttpHost("localhost", 9200, "http"))
//                .setEmitter(new ElasticsearchEmitter<FanDevice>() {
//                    @Override
//                    public void emit(FanDevice temp, SinkWriter.Context context, RequestIndexer requestIndexer) {
//                        Map<String, Object> dataMap = new HashMap<>();
//                        dataMap.put("id", temp.getIdFan() != null ? temp.getIdFan().toString() : "");
//                        dataMap.put("Status", temp.getBbcName() != null ? temp.getBbcName().toString() : "");
//                        dataMap.put("Speed", temp.getBbcControlFan() != null ? temp.getBbcControlFan().toString() : "0");
//                        dataMap.put("Timestamp", temp.getTimestamp() != null ? Timestamp.valueOf(LocalDateTime.parse(temp.getTimestamp().toString(), formatter)) : null);
//                        dataMap.put("Fan_Status", temp.getBbcFan() != null ? temp.getBbcFan().toString() : "0");
//                        requestIndexer.add(Requests.indexRequest()
//                                .index("FanDevice")
//                                .id(temp.getIdFan().toString() + temp.getTimestamp().toString())
//                                .source(dataMap));
//                    }
//                })
//                .setBulkFlushMaxActions(1000)
//                .setBulkFlushMaxSizeMb(5)
//                .setBulkFlushInterval(1000).build()).name("Fan Device Sink");
//
        DoorData.addSink(JdbcSink.sink(
                "INSERT INTO Lock (device_id, name, status, location, password) VALUES (?, ?, ?, ?, ?) " +
                        "ON CONFLICT (device_id) " +
                        "DO UPDATE SET " +
                        "   name = COALESCE(EXCLUDED.name, Lock.name), " +
                        "   status = COALESCE(EXCLUDED.status, Lock.status), " +
                        "   location = COALESCE(EXCLUDED.location, Lock.location), " +
                        "   password = COALESCE(EXCLUDED.password, Lock.password)",
                (JdbcStatementBuilder<DoorDevice>) (ps, t) -> {
                    ps.setString(1, t.getIdDoor() != null ? t.getIdDoor().toString() : null);
                    ps.setString(2, null);
                    ps.setBoolean(3, t.getBbcServo() != null && !t.getBbcServo().toString().equals("0"));
                    ps.setString(4, null);
                    ps.setString(5, t.getBbcPassword() != null ? t.getBbcPassword().toString() : null);
                },
                jobExecutionOptions,
                connectionOptions
        ));

        DoorData.addSink(JdbcSink.sink(
                "INSERT INTO Control (device_id, username, control_time) VALUES (?, ?, ?) " +
                        "ON CONFLICT (device_id, username, control_time) DO NOTHING",
                (JdbcStatementBuilder<DoorDevice>) (ps, doorDevice) -> {
                    ps.setString(1, doorDevice.getIdDoor() != null ? doorDevice.getIdDoor().toString() : null);
                    ps.setString(2, doorDevice.getBbcName() != null ? doorDevice.getBbcName().toString() : null);
                    ps.setString(3, doorDevice.getTimestamp() != null ? doorDevice.getTimestamp().toString() : null);
                },
                jobExecutionOptions,
                connectionOptions
        ));

//        DoorData.sinkTo(new Elasticsearch7SinkBuilder<DoorDevice>()
//                .setHosts(new HttpHost("localhost", 9200, "http"))
//                .setEmitter(new ElasticsearchEmitter<DoorDevice>() {
//                    @Override
//                    public void emit(DoorDevice temp, SinkWriter.Context context, RequestIndexer requestIndexer) {
//                        Map<String, Object> dataMap = new HashMap<>();
//                        dataMap.put("id", temp.getIdDoor() != null ? temp.getIdDoor().toString() : "");
//                        dataMap.put("Status", temp.getBbcName() != null ? temp.getBbcName().toString() : "");
//                        dataMap.put("Password", temp.getBbcPassword() != null ? temp.getBbcPassword().toString() : "");
//                        dataMap.put("Timestamp", temp.getTimestamp() != null ? Timestamp.valueOf(LocalDateTime.parse(temp.getTimestamp().toString(), formatter)
//                        ) : null);
//                        dataMap.put("Door_Status", temp.getBbcServo() != null ? temp.getBbcServo().toString() : "0");
//                        requestIndexer.add(Requests.indexRequest()
//                                .index("DoorDevice")
//                                .id(temp.getIdDoor().toString() + temp.getTimestamp().toString())
//                                .source(dataMap));
//                    }
//                })
//                .setBulkFlushMaxActions(1000)
//                .setBulkFlushMaxSizeMb(5)
//                .setBulkFlushInterval(1000).build()).name("Door Device Sink");

        LedData.addSink(JdbcSink.sink(
                "INSERT INTO Light (device_id, name, status, location) VALUES (?, ?, ?, ?) " +
                        "ON CONFLICT (device_id) " +
                        "DO UPDATE SET " +
                        "   name = COALESCE(EXCLUDED.name, Light.name), " +
                        "   status = COALESCE(EXCLUDED.status, Light.status), " +
                        "   location = COALESCE(EXCLUDED.location, Light.location)",
                (JdbcStatementBuilder<LedDevice>) (ps, t) -> {
                    ps.setString(1, t.getIdLed() != null ? t.getIdLed().toString() : null);
                    ps.setString(2, null);
                    ps.setBoolean(3, t.getBbcLed() != null && !t.getBbcLed().toString().equals("0"));
                    ps.setString(4, null);
                },
                jobExecutionOptions,
                connectionOptions
        ));

        LedData.addSink(JdbcSink.sink(
                "INSERT INTO Control (device_id, username, control_time) VALUES (?, ?, ?) " +
                        "ON CONFLICT (device_id, username, control_time) DO NOTHING",
                (JdbcStatementBuilder<LedDevice>) (ps, ledDevice) -> {
                    ps.setString(1, ledDevice.getIdLed() != null ? ledDevice.getIdLed().toString() : null);
                    ps.setString(2, ledDevice.getBbcName() != null ? ledDevice.getBbcName().toString() : null);
                    ps.setString(3, ledDevice.getTimestamp() != null ? ledDevice.getTimestamp().toString() : null);
                },
                jobExecutionOptions,
                connectionOptions
        ));

//        LedData.sinkTo(new Elasticsearch7SinkBuilder<LedDevice>()
//                .setHosts(new HttpHost("localhost", 9200, "http"))
//                .setEmitter(new ElasticsearchEmitter<LedDevice>() {
//                    @Override
//                    public void emit(LedDevice temp, SinkWriter.Context context, RequestIndexer requestIndexer) {
//                        Map<String, Object> dataMap = new HashMap<>();
//                        dataMap.put("id", temp.getIdLed() != null ? temp.getIdLed().toString() : "");
//                        dataMap.put("Status", temp.getBbcName() != null ? temp.getBbcName().toString() : "");
//                        dataMap.put("Timestamp", temp.getTimestamp() != null ? Timestamp.valueOf(LocalDateTime.parse(temp.getTimestamp().toString(), formatter)) : null);
//                        dataMap.put("Led_Status", temp.getBbcLed() != null ? temp.getBbcLed().toString() : "0");
//                        requestIndexer.add(Requests.indexRequest()
//                                .index("LedDevice")
//                                .id(temp.getIdLed().toString() + temp.getTimestamp().toString())
//                                .source(dataMap));
//                    }
//                })
//                .setBulkFlushMaxActions(1000)
//                .setBulkFlushMaxSizeMb(5)
//                .setBulkFlushInterval(1000).build()).name("Led Device Sink");

        avgTempStream.addSink(JdbcSink.sink(
                "INSERT INTO Temperature (location, record_time, value) VALUES (?, ?, ?) " +
                        "ON CONFLICT (location, record_time) DO NOTHING",
                (JdbcStatementBuilder<Tuple5<String, Double, String, String, String>>) (ps, t) -> {
                    ps.setString(1, t.f0 != null ? t.f0 : null);
                    ps.setString(2, t.f4 != null ? t.f4 : null);
                    ps.setDouble(3, t.f1);
                },
                jobExecutionOptions,
                connectionOptions
        ));

        avgHempStream.addSink(JdbcSink.sink(
                "INSERT INTO Humidity (location, record_time, value) VALUES (?, ?, ?) " +
                        "ON CONFLICT (location, record_time) DO NOTHING",
                (JdbcStatementBuilder<Tuple5<String, Double, String, String, String>>) (ps, t) -> {
                    ps.setString(1, t.f0 != null ? t.f0 : null);
                    ps.setString(2, t.f4 != null ? t.f4 : null);
                    ps.setDouble(3, t.f1);
                },
                jobExecutionOptions,
                connectionOptions
        ));

        ElasticsearchSink<Tuple5<String, Double, String, String, String>> esSink =
                new Elasticsearch7SinkBuilder<Tuple5<String, Double, String, String, String>>()
                        .setHosts(new HttpHost("localhost", 9200, "http"))
                        .setEmitter((element, context, indexer) -> {
                            Map<String, Object> dataMap = new HashMap<>();
                            dataMap.put("id", Objects.requireNonNullElse(element.f0, ""));
                            dataMap.put("timestamp", Objects.requireNonNullElse(element.f4, ""));
                            dataMap.put("value", Objects.requireNonNullElse(element.f1, 0.0));

                            String docId = Objects.requireNonNullElse(element.f0, "") +
                                    Objects.requireNonNullElse(element.f4, "");

                            IndexRequest request = Requests.indexRequest()
                                    .index("temperature")
                                    .id(docId)
                                    .source(dataMap);

                            indexer.add(request);
                        })
                        .setBulkFlushMaxActions(50)
                        .setBulkFlushInterval(5000)
                        .build();

        avgTempStream.sinkTo(esSink).name("Temperature Metrics Sink").setParallelism(4);;

        // Configure Elasticsearch sink for average temperature data
//        avgTempStream.sinkTo(
//                new Elasticsearch7SinkBuilder<Tuple5<String, Double, String, String, String>>()
//                        .setBulkFlushMaxActions(1)
//                        .setHosts(new HttpHost("localhost", 9200, "http"))
//                        .setEmitter((element, context, indexer) -> {
//                            Map<String, Object> dataMap = new HashMap<>();
//                            dataMap.put("id", element.f0 != null ? element.f0 : "");
//                            dataMap.put("timestamp", element.f4 != null ? Timestamp.valueOf(LocalDateTime.parse(element.f4, formatter)) : null);
//                            dataMap.put("value", element.f1 != null ? element.f1 : 0.0);
//                            indexer.add(Requests.indexRequest()
//                                    .index("AvgTemp")
//                                    .id(element.f0 + element.f4)
//                                    .source(dataMap));
//                        }).build()
//        );
//        // Configure Elasticsearch sink for average temperature data
//        Elasticsearch7SinkBuilder<Tuple5<String, Double, String, String, String>> esSinkBuilder =
//                new Elasticsearch7SinkBuilder<Tuple5<String, Double, String, String, String>>()
//                        .setHosts(new HttpHost("localhost", 9200, "http"))
//                        .setBulkFlushMaxActions(1)
//                        .setEmitter(new ElasticsearchEmitter<Tuple5<String, Double, String, String, String>>() {
//                            @Override
//                            public void emit(Tuple5<String, Double, String, String, String> element, SinkWriter.Context context, RequestIndexer requestIndexer) {
//                                System.out.println("Data to Elasticsearch: " + element);
//
//                                // Kiểm tra dữ liệu hợp lệ
//                                if (element.f0 == null || element.f0.isEmpty() ||
//                                        element.f1 == null ||
//                                        element.f2 == null || element.f2.isEmpty() ||
//                                        element.f4 == null || element.f4.isEmpty()) {
//                                    System.err.println("Dữ liệu không hợp lệ, bỏ qua: " + element);
//                                    return;
//                                }
//
//                                Map<String, Object> document = new HashMap<>();
//                                document.put("id", element.f0);
//                                document.put("temperature", element.f1);
//                                document.put("name", element.f2);
//                                document.put("timestamp", element.f4);
//
//                                IndexRequest request = Requests.indexRequest()
//                                        .index("test")
//                                        .source(document, XContentType.JSON);
//
//                                try {
//                                    requestIndexer.add(request);
//                                } catch (Exception e) {
//                                    e.printStackTrace();
//                                }
//                            }
//                        });

        // Ghi vào Elasticsearch
//        avgTempStream.sinkTo(esSinkBuilder.build()).name("Temperature Metrics Sink");

//        avgHempStream.sinkTo(new Elasticsearch7SinkBuilder<Tuple5<String, Double, String, String, String>>()
//                .setHosts(new HttpHost("localhost", 9200, "http"))
//                .setEmitter(new ElasticsearchEmitter<Tuple5<String, Double, String, String, String>>() {
//                    @Override
//                    public void emit(Tuple5<String, Double, String, String, String> element, SinkWriter.Context context, RequestIndexer requestIndexer) {
//                        Map<String, Object> dataMap = new HashMap<>();
//                        dataMap.put("id", element.f0 != null ? element.f0 : "");
//                        dataMap.put("timestamp", element.f4 != null ? Timestamp.valueOf(LocalDateTime.parse(element.f4, formatter)) : null);
//                        dataMap.put("value", element.f1 != null ? element.f1 : 0.0);
//                        requestIndexer.add(Requests.indexRequest()
//                                .index("AvgHem")
//                                .id(element.f0 + element.f4)
//                                .source(dataMap));
//                    }
//                })
//                .setBulkFlushMaxActions(1000)
//                .setBulkFlushMaxSizeMb(5)
//                .setBulkFlushInterval(1000).build()).name("Average Hum Sink");

        env.execute("YoloHome IoT Data Processing");
    }
}

class MapFunctionTemp implements MapFunction<TempDevice, Tuple5<String, Double, String, String, String>> {
    @Override
    public Tuple5<String, Double, String, String, String> map(TempDevice temp) throws Exception {
        return new Tuple5<String, Double, String, String, String>(temp.getIdTemp().toString(), Double.valueOf(temp.getBbcTemp()), temp.getBbcName().toString(), temp.getBbcPassword().toString(), temp.getTimestamp().toString());
    }

}

class MapFunctionHum implements MapFunction<HumidityDevice, Tuple5<String, Double, String, String, String>> {
    @Override
    public Tuple5<String, Double, String, String, String> map(HumidityDevice hum) throws Exception {
        return new Tuple5<String, Double, String, String, String>(hum.getIdHum().toString(), Double.valueOf(hum.getBbcHum()), hum.getBbcName().toString(), hum.getBbcPassword().toString(), hum.getTimestamp().toString());
    }
}

class AverageAggregate implements AggregateFunction<Tuple5<String, Double, String, String, String>, Tuple6<String, Double, String, String, String, Long>, Tuple5<String, Double, String, String, String>> {
    @Override
    public Tuple6<String, Double, String, String, String, Long> createAccumulator() {
        return new Tuple6<>(null, 0.0, null, null, null, 0L);
    }

    @Override
    public Tuple6<String, Double, String, String, String, Long> add(Tuple5<String, Double, String, String, String> value, Tuple6<String, Double, String, String, String, Long> accumulator) {
        return new Tuple6<>(
                accumulator.f0 != null ? accumulator.f0 : value.f0,
                accumulator.f1 + value.f1,
                accumulator.f2 != null ? accumulator.f2 : value.f2,
                accumulator.f3 != null ? accumulator.f3 : value.f3,
                accumulator.f4 != null ? accumulator.f4 : value.f4,
                accumulator.f5 + 1L
        );
    }

    @Override
    public Tuple5<String, Double, String, String, String> getResult(Tuple6<String, Double, String, String, String, Long> accumulator) {
        return new Tuple5<>(
                accumulator.f0,
                accumulator.f5 > 0 ? accumulator.f1 / accumulator.f5 : 0.0,
                accumulator.f2,
                accumulator.f3,
                accumulator.f4
        );
    }

    @Override
    public Tuple6<String, Double, String, String, String, Long> merge(Tuple6<String, Double, String, String, String, Long> obj1, Tuple6<String, Double, String, String, String, Long> obj2) {
        return new Tuple6<>(
                obj1.f0,
                obj1.f1 + obj2.f1,
                obj1.f2,
                obj1.f3,
                obj1.f4,
                obj1.f5 + obj2.f5
        );
    }
}