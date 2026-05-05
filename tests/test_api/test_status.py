from src.api.routes.status import router


def test_status_router_has_list_endpoint():
    paths = [r.path for r in router.routes]
    assert any("applications" in str(p) for p in paths)


def test_status_router_has_detail_endpoint():
    paths = [r.path for r in router.routes]
    assert any("{application_id}" in str(p) for p in paths)
