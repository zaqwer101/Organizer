from shared import *
import shared


@pytest.fixture(autouse=True)
def before():
    shared._before()


def test_add_success():
    """ добавление элемента в список. Успешные сценарии """
    token = register('test', 'testpassword')
    request('POST', '/shoplist', {"name": "item1", "token": token, "shop": "shop1"})
    data = get_shoplist_items(token)
    print(data)
    assert len(data) == 1
    assert data[0]['name'] == 'item1'
    assert data[0]['user'] == 'test'
    assert data[0]['bought'] == 'false'
    assert data[0]['shop'] == 'shop1'
    assert data[0]['amount'] == 1

    # одинаковое имя, но разные магазины
    request('POST', '/shoplist', {"name": "item1", "token": token})
    data = get_shoplist_items(token)
    assert len(data) == 2
    assert data[0]['amount'] == 1

    # одинаковое имя и одинаковые магазины
    request('POST', '/shoplist', {"name": "item1", "token": token, "shop": "shop1"})
    data = get_shoplist_items(token)
    assert len(data) == 2 # не меняется с прошлой итерации, потому что элемент должен сложиться к другому
    assert data[0]['amount'] == 2


def test_delete_success():
    token = register('test', 'testpassword')
    request('POST', '/shoplist', {"name": "item1", "token": token})
    data = get_shoplist_items(token)
    assert data[0]['name'] == 'item1'

    request('DELETE', '/shoplist', {"name": "item1", "token": token})
    data = get_shoplist_items(token)
    assert len(data) == 0
    

def test_setbought_success():
    token = register('test', 'testpassword')
    request('POST', '/shoplist', {"name": "item1", "token": token})
    data = get_shoplist_items(token)
    assert data[0]['bought'] == 'false'

    request('POST', '/shoplist/bought', {"name": "item1", "token": token, "bought": "true"})
    data = get_shoplist_items(token)
    assert data[0]['bought'] == 'true'