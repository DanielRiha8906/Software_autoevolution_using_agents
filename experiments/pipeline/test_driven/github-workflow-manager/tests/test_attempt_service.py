import pytest
from datetime import datetime, timezone, timedelta
from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.services.attempt_service import AttemptService


CEST = timezone(timedelta(hours=2))


def _attempt(run_id=1, attempt_number=1):
    return WorkflowRunAttempt(
        id=attempt_number,
        run_id=run_id,
        attempt_number=attempt_number,
        status="completed",
        conclusion="success",
        created_at=datetime.now(CEST),
    )


def test_attempt_service_exists():
    assert AttemptService() is not None


def test_create_attempt():
    svc = AttemptService()
    attempt = svc.create(_attempt())
    assert attempt is not None


def test_retrieve_attempts_by_run_id():
    svc = AttemptService()
    svc.create(_attempt(run_id=1, attempt_number=1))
    svc.create(_attempt(run_id=1, attempt_number=2))
    svc.create(_attempt(run_id=2, attempt_number=1))

    results = svc.get_by_run_id(1)

    assert len(results) == 2
    assert all(a.run_id == 1 for a in results)


def test_duplicate_attempt_number_raises():
    svc = AttemptService()
    svc.create(_attempt(run_id=1, attempt_number=1))

    with pytest.raises(Exception):
        svc.create(_attempt(run_id=1, attempt_number=1))


def test_attempts_sorted_by_attempt_number():
    svc = AttemptService()
    svc.create(_attempt(run_id=1, attempt_number=2))
    svc.create(_attempt(run_id=1, attempt_number=1))

    results = svc.get_by_run_id(1)

    assert results[0].attempt_number < results[1].attempt_number


def test_attempt_service_does_not_contain_file_io():
    import inspect
    from src.services import attempt_service as mod
    source = inspect.getsource(mod)

    assert "open(" not in source
    assert "json.dump" not in source
