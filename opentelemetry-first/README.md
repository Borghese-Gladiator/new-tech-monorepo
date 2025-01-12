# OpenTelemetry

OpenTelemetry is an open-source observability framework designed to collect, process, and export telemetry data, such as traces, metrics, and logs, from applications. It provides a set of APIs, SDKs, and tools to enable developers to understand and monitor the behavior and performance of distributed systems. OpenTelemetry is vendor-neutral, meaning it can integrate with various backends like Prometheus, Jaeger, Zipkin, or commercial observability platforms.

[OpenTelemetry Demo](https://opentelemetry.io/ecosystem/demo/) - note it takes super long to download containers

## Telemtery Data Types

- **Traces**: Represent a series of events or operations (spans) within a distributed system. Traces provide end-to-end visibility into requests across services.
- **Metrics**: Quantitative measurements, such as request latency, error counts, and system resource usage (CPU, memory).
- **Logs**: Structured or unstructured data that records discrete events during an application's execution.

## Components

#### a. **APIs**

The APIs allow developers to instrument their applications with tracing, metrics, and logs. They are language-specific and designed to integrate seamlessly with existing codebases.

#### b. **SDKs**

SDKs implement the APIs and handle the configuration and processing of telemetry data, including batching and exporting to various backends.

#### c. **Instrumentation Libraries**

Pre-built libraries for common frameworks and libraries (e.g., HTTP clients, databases) automatically capture telemetry data without requiring significant manual effort.

#### d. **Exporters**

Exporters send processed telemetry data to an observability backend, such as Prometheus, Jaeger, or Google Cloud Trace.

#### e. **Collectors**

The OpenTelemetry Collector is a standalone service that receives telemetry data from applications, processes it (e.g., sampling, filtering), and exports it to backends.

## Usage
1. **Instrumentation** - add observability code to application for telemetry
   - install dependencies
     ```
      pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-jaeger
     ```
   - Automatic Instrumentation
     - use in conjunction with manual for additional metrics specific to your application
     ```bash
       pip install opentelemetry-instrumentation-flask
       opentelemetry-instrument --traces_exporter console flask run app:app
     ```
   - Manual Instrumentation via OpenTelemetry API and SDK
     ```python
      from opentelemetry import trace
      from opentelemetry.sdk.trace import TracerProvider
      from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
      # Set up tracer provider and exporter
      trace.set_tracer_provider(TracerProvider())
      tracer = trace.get_tracer(__name__)
      span_processor = BatchSpanProcessor(ConsoleSpanExporter())
      trace.get_tracer_provider().add_span_processor(span_processor)
      # Create a trace
      with tracer.start_as_current_span("example-span"):
          print("Hello, OpenTelemetry!")
     ```
     - use OpenTelemetry to create spans, metrics, and logs

2. **Set Up Tracer/Meter Providers**
   - Configure a **TracerProvider** for traces and a **MeterProvider** for metrics.
   - Customize providers as needed (e.g., sampling strategies, resource attributes).
     ```python
     from opentelemetry.sdk.trace import TracerProvider
     from opentelemetry import trace

     trace.set_tracer_provider(TracerProvider())
     tracer = trace.get_tracer(__name__)
     ```

3. **Configure Exporters**
   - Export telemetry data to a backend for visualization and analysis. Examples:
     - **Traces**:
       - `opentelemetry-exporter-jaeger` for exporting traces to Jaeger.
       - `opentelemetry-exporter-otlp` for exporting to OpenTelemetry Protocol (OTLP)-compatible backends.
     - **Metrics**:
       - `opentelemetry-exporter-prometheus` for Prometheus metrics scraping.
     ```bash
     pip install opentelemetry-exporter-jaeger opentelemetry-exporter-prometheus
     ```

4. **Set Up Processors**
   - Use processors to manage telemetry data before exporting:
     - **Span Processors**:
       - `SimpleSpanProcessor` for immediate export of spans (development).
       - `BatchSpanProcessor` for efficient batching of spans (production).
     ```python
     from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

     span_processor = BatchSpanProcessor(ConsoleSpanExporter())
     trace.get_tracer_provider().add_span_processor(span_processor)
     ```

5. **Run an OpenTelemetry Collector (Optional)**
   - Use the **OpenTelemetry Collector** to centralize telemetry processing. Configure it to:
     - Receive telemetry data via OTLP or other protocols.
     - Process data (e.g., filter, sample, or aggregate).
     - Export to multiple backends (e.g., Jaeger, Prometheus, or Elasticsearch).
   - Example: Configure a YAML pipeline for the Collector:
     ```yaml
     receivers:
       otlp:
         protocols:
           grpc:
           http:
     exporters:
       jaeger:
         endpoint: "http://jaeger-collector:14250"
       prometheus:
         endpoint: "0.0.0.0:8888"
     service:
       pipelines:
         traces:
           receivers: [otlp]
           processors: []
           exporters: [jaeger]
         metrics:
           receivers: [otlp]
           processors: []
           exporters: [prometheus]
     ```

6. **Integrate Context Propagation**
   - Ensure distributed systems use consistent context propagation to correlate spans:
     - Use the `W3CTraceContext` propagator for HTTP headers like `traceparent` and `tracestate`.
     ```python
     from opentelemetry.propagators import set_global_textmap
     from opentelemetry.propagators.tracecontext import TraceContextTextMapPropagator

     set_global_textmap(TraceContextTextMapPropagator())
     ```

7. **Visualize and Analyze Telemetry Data**
   - Use observability platforms to visualize the collected data:
     - Traces: View in **Jaeger** or **Zipkin**.
     - Metrics: Monitor in **Prometheus** or **Grafana**.
     - Logs: Integrate with **Elasticsearch** or **Loki** for centralized logging.


## Benefits of OpenTelemetry
1. Vendor-Agnostic: Flexibility to choose or switch between observability backends.
2. Unified Observability: Combine traces, metrics, and logs for a comprehensive view.
3. Wide Language Support: Supports major programming languages.
4. Rich Ecosystem: Pre-built instrumentation libraries for popular frameworks.
5. Future-Proof: Community-driven and supported by major vendors.
