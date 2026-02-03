def test_create_todo_and_retrieve_it(client):
    """Create a Todo item and then retrieve it to verify it exists."""
    response = client.post(
        "/todos",
        json={
            "title": "Test",
            "description": "Test description",
            "completed": False,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test"
    assert data["description"] == "Test description"
    assert data["completed"] is False
    assert "id" in data
    todo_id = data["id"]

    get_response = client.get(f"/todos/{todo_id}")
    assert get_response.status_code == 200
    retrieved = get_response.json()
    assert retrieved["id"] == todo_id
    assert retrieved["title"] == "Test"
    assert retrieved["description"] == "Test description"
    assert retrieved["completed"] is False
