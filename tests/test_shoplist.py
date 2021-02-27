from shared import *
import shared


@pytest.fixture(autouse=True)
def before():
    shared._before()


def test_add():
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


def test_add_multiple_shops():
    token = register('test', 'testpassword')
    request('POST', '/shoplist', {"name": "item3", "token": token, "shop": "shop2"})
    request('POST', '/shoplist', {"name": "item3", "token": token, "shop": "shop2"})
    request('POST', '/shoplist', {"name": "item3", "token": token, "shop": "shop2"})
    request('POST', '/shoplist', {"name": "item3", "token": token, "shop": "shop2"})
    request('POST', '/shoplist', {"name": "item3", "token": token, "shop": "shop2"})
    data = get_shoplist_items(token)
    assert data[0]['shop'] == 'shop2'
    assert data[0]['amount'] == 5


def test_delete_with_shop():
    token = register('test', 'testpassword')
    request('POST', '/shoplist', {"name": "item1", "token": token, "shop": "shop1"})
    data = get_shoplist_items(token)
    assert data[0]['name'] == 'item1'

    request('DELETE', '/shoplist', {"name": "item1", "token": token, "shop": "shop1"})
    data = get_shoplist_items(token)
    assert len(data) == 0

    request('POST', '/shoplist', {"name": "item1", "token": token, "shop": "shop1"})
    data = get_shoplist_items(token)
    assert data[0]['name'] == 'item1'

    request('DELETE', '/shoplist', {"name": "item1", "token": token, "shop": "shop2"})
    data = get_shoplist_items(token)
    assert len(data) == 1 # удалиться не должен, т.к. магазины не совпадают


def test_delete_without_shop():
    token = register('test', 'testpassword')
    request('POST', '/shoplist', {"name": "item1", "token": token, "shop": "shop1"})
    data = get_shoplist_items(token)
    assert data[0]['name'] == 'item1'

    request('DELETE', '/shoplist', {"name": "item1", "token": token})
    data = get_shoplist_items(token)
    assert len(data) == 1 # удалиться не должен, т.к. магазин передан как null
    

def test_setbought():
    token = register('test', 'testpassword')
    request('POST', '/shoplist', {"name": "item1", "token": token})
    data = get_shoplist_items(token)
    assert data[0]['bought'] == 'false'

    request('POST', '/shoplist/bought', {"name": "item1", "token": token, "bought": "true"})
    data = get_shoplist_items(token)
    assert data[0]['bought'] == 'true'