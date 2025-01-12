from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

# Step 1: Set up the tracer provider and exporter
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Add a span processor to send trace data to the console
span_processor = SimpleSpanProcessor(ConsoleSpanExporter())
trace.get_tracer_provider().add_span_processor(span_processor)

# Step 2: Create and use spans to trace operations
def do_work():
    # Create a parent span
    with tracer.start_as_current_span("parent-span") as parent_span:
        parent_span.set_attribute("example.key", "parent-value")

        # Create a child span
        with tracer.start_as_current_span("child-span") as child_span:
            child_span.set_attribute("example.key", "child-value")
            print("Doing some work inside the child span...")

if __name__ == "__main__":
    print("Starting OpenTelemetry simple tracing demo...")
    do_work()
    print("Tracing complete.")


"""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.semconv.trace import SpanAttributes

provider = TracerProvider()
processor = BatchSpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(processor)

# Sets the global default tracer provider
trace.set_tracer_provider(provider)

# Creates a tracer from the global tracer provider
tracer = trace.get_tracer("my.tracer.name")


def do_work():
    with tracer.start_as_current_span("parent") as parent:
        # do some work that 'parent' tracks
        print("doing some work...")
        # Create a nested span to track nested work
        with tracer.start_as_current_span("child") as child:
            # do some work that 'child' tracks
            print("doing some nested work...")
            # the nested span is closed when it's out of scope

        # This span is also closed when it goes out of scope

@tracer.start_as_current_span("do_work")
def do_work():
    print("doing some work...")

current_span = trace.get_current_span()

current_span.set_attribute(SpanAttributes.HTTP_METHOD, "GET")
current_span.set_attribute(SpanAttributes.HTTP_URL, "https://opentelemetry.io/")

current_span.set_attribute("operation.value", 1)
current_span.set_attribute("operation.name", "Saying hello!")
current_span.set_attribute("operation.other-stuff", [1, 2, 3])

current_span.add_event("Gonna try it!")
current_span.add_event("Did it!")
"""