import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# OpenTelemetry imports
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup OpenTelemetry
resource = Resource(attributes={
    "service.name": "backend-service"
})
tracer_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(tracer_provider)

otlp_trace_exporter = OTLPSpanExporter(endpoint="http://otel-collector:4318/v1/traces")
span_processor = BatchSpanProcessor(otlp_trace_exporter)
tracer_provider.add_span_processor(span_processor)

metric_exporter = OTLPMetricExporter(endpoint="http://otel-collector:4318/v1/metrics")
metric_reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=5000)
meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter(__name__)

items_created_counter = meter.create_counter(
    "items_created",
    description="Number of items created"
)

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_NAME = os.getenv("DB_NAME", "my_database")
DB_USER = os.getenv("DB_USER", "my_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "my_password")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

app = FastAPI()

class Item(BaseModel):
    data: str

@app.post("/items")
def create_item(item: Item):
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("create_item"):
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("INSERT INTO items (data) VALUES (%s) RETURNING id", (item.data,))
                new_id = cur.fetchone()[0]
                conn.commit()
                logger.info(f"Created item with id {new_id}")
                items_created_counter.add(1)
                return {"id": new_id, "data": item.data}
        except Exception as e:
            logger.error(f"Error creating item: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/items")
def read_items():
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("read_items"):
        try:
            conn = get_db_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, data FROM items ORDER BY id DESC")
                results = cur.fetchall()
                return {"items": results}
        except Exception as e:
            logger.error(f"Error reading items: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
