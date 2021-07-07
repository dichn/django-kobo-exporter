from django.http.response import HttpResponse

from prometheus_client import (
    CollectorRegistry,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

from kobo.hub.models import Worker


class Metrics(object):
    # Container for all supported metrics.

    def __init__(self):
        self.registry = CollectorRegistry(auto_describe=True)

        self.worker_enabled = Gauge(
            "kobo_worker_enabled",
            "1 if worker is enabled",
            labelnames=["worker"],
            registry=self.registry,
        )

        self.worker_ready = Gauge(
            "kobo_worker_ready",
            "1 if worker is ready",
            labelnames=["worker"],
            registry=self.registry,
        )

        self.worker_load = Gauge(
            "kobo_worker_load",
            "Current load of worker (sum of task weights)",
            labelnames=["worker"],
            registry=self.registry,
        )

        self.worker_max_load = Gauge(
            "kobo_worker_max_load",
            "Maximum permitted load of worker",
            labelnames=["worker"],
            registry=self.registry,
        )

        self.worker_open_tasks = Gauge(
            "kobo_worker_open_tasks",
            "Current number of OPEN tasks for worker",
            labelnames=["worker"],
            registry=self.registry,
        )

        self.worker_last_seen = Gauge(
            "kobo_worker_last_seen_seconds",
            "Time of worker's last communication with hub",
            labelnames=["worker"],
            unit="seconds",
            registry=self.registry,
        )

    def as_string(self):
        return generate_latest(self.registry)


def metrics_string(workers):
    metrics = Metrics()

    getters = [
        (metrics.worker_enabled, lambda w: 1 if w.enabled else 0),
        (metrics.worker_ready, lambda w: 1 if w.enabled else 0),
        (metrics.worker_load, lambda w: w.current_load),
        (metrics.worker_max_load, lambda w: w.max_load),
        (metrics.worker_open_tasks, lambda w: w.task_count),
        (
            metrics.worker_last_seen,
            lambda w: int(w.last_seen.timestamp()) if w.last_seen else 0,
        ),
    ]

    for worker in workers:
        for (metric, fn) in getters:
            value = fn(worker)
            metric.labels(worker=worker).set(value)

    return metrics.as_string()


def metrics(_request):
    workers = Worker.objects.order_by("name")

    return HttpResponse(
        metrics_string(workers),
        content_type=CONTENT_TYPE_LATEST,
    )
