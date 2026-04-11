def test_list_news(client):
    response = client.get("/api/v1/news")

    assert response.status_code == 200
    assert isinstance(response.json(), list)