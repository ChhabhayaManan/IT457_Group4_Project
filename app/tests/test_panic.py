from panic import PanicFlag


class FakeSSM:
    """Stands in for the boto3 SSM client: returns queued values, raises queued errors."""

    def __init__(self, *results):
        self.results = list(results)

    def get_parameter(self, Name):
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return {"Parameter": {"Name": Name, "Value": result}}


def test_reads_on_from_ssm():
    flag = PanicFlag("/group4-hotstar/panic-mode", client=FakeSSM("on"))
    flag.refresh()
    assert flag.is_on() is True


def test_reads_off_from_ssm():
    flag = PanicFlag("/group4-hotstar/panic-mode", client=FakeSSM("off"))
    flag.refresh()
    assert flag.is_on() is False


def test_keeps_last_value_when_ssm_fails():
    flag = PanicFlag("/group4-hotstar/panic-mode", client=FakeSSM("on", RuntimeError("throttled")))
    flag.refresh()
    flag.refresh()
    assert flag.is_on() is True


def test_off_when_first_read_fails():
    flag = PanicFlag("/group4-hotstar/panic-mode", client=FakeSSM(RuntimeError("no credentials")))
    flag.refresh()
    assert flag.is_on() is False


def test_env_fallback_without_param(monkeypatch):
    flag = PanicFlag(None)
    monkeypatch.setenv("PANIC_MODE", "on")
    assert flag.is_on() is True
    monkeypatch.setenv("PANIC_MODE", "off")
    assert flag.is_on() is False
