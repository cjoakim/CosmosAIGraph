import pytest

from src.services.config_service import ConfigService
from src.services.entities_service import EntitiesService
from src.util.counter import Counter

# pytest tests/test_entities_service.py

@pytest.mark.asyncio
def test_build_with_libraries_mini_nt_and_owl_file():
    ConfigService.set_standard_unit_test_env_vars()
    entities_svc = EntitiesService()
    await entities_svc.initialize()

    assert entities_svc.libraries_count() > 10000  # 10761
    assert entities_svc.libraries_count() < 20000

    assert entities_svc.library_present("flask") == True
    assert entities_svc.library_present("pydantic-core") == True
    assert entities_svc.library_present("pypi") == False
    # case 1
    counter: Counter = entities_svc.identify(None)
    assert counter is not None
    print(counter.get_data())
    assert counter.most_frequent() == None

    # case 2
    counter: Counter = entities_svc.identify("")
    assert counter is not None
    print(counter.get_data())
    assert counter.most_frequent() == None

    # case 3
    counter: Counter = entities_svc.identify("Chris, Aleksey, Luciano")
    assert counter is not None
    print(counter.get_data())
    assert counter.most_frequent() == None

    # case 4
    counter: Counter = entities_svc.identify("i have a flask of water")
    assert counter is not None
    print(counter.get_data())
    assert counter.most_frequent() == "flask"

    # case 5
    counter: Counter = entities_svc.identify("I want to express how much I like Fastapi, pydantic, you, and fastapi")
    assert counter is not None
    print(counter.get_data())  # {'express': 1, 'fastapi': 2, 'pydantic': 1}
    assert counter.most_frequent() == "fastapi"
    assert counter.get_data()["pydantic"] == 1
    assert counter.get_data()["fastapi"] == 2
