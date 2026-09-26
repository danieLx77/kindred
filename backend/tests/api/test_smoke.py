async def test_rota_raiz_responde_ok(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
