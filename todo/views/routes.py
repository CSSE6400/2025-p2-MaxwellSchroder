from flask import Blueprint, jsonify, request
from todo.models import db
from todo.models.todo import Todo
from datetime import datetime, timedelta

api = Blueprint('api', __name__, url_prefix='/api/v1') 

TEST_ITEM = {
    "id": 1,
    "title": "Watch CSSE6400 Lecture",
    "description": "Watch the CSSE6400 lecture on ECHO360 for week 1",
    "completed": True,
    "deadline_at": "2023-02-27T00:00:00",
    "created_at": "2023-02-20T00:00:00",
    "updated_at": "2023-02-20T00:00:00"
}
 
@api.route('/health') 
def health():
    """Return a status of 'ok' if the server is running and listening to request"""
    return jsonify({"status": "ok"})

def str_to_bool(value):
    if value is None:
        return None  # Don't apply any filter
    val = value.lower()
    if val == 'true':
        return True
    elif val == 'false':
        return False
    return None  # For invalid values like "maybe"

# GET TODO with full functionality
@api.route("/todos", methods=["GET"])
def get_todos():
    completed = request.args.get("completed")
    window = request.args.get("window", type=int) #get int from parameter, otherwise its none

    query = Todo.query # select * from Todo table

    if completed: # only run completed filter if it has valid values true or false, all others don't apply filter
        completed_bool = str_to_bool(completed)
        if completed_bool is not None:
            query = query.filter_by(completed=completed_bool)
        else:
            return jsonify({"error":"incorrect completed parameter"}), 400
    if window is not None:
        today = datetime.now()
        deadline_limit = today + timedelta(days=window)

        query = query.filter(Todo.deadline_at != None)
        query = query.filter(Todo.deadline_at <= deadline_limit)
        query = query.filter(Todo.deadline_at >= datetime.now())

    todos = query.all()
    result = []
    for todo in todos:
        result.append(todo.to_dict())
    return jsonify(result)


### Get single item from todo list
@api.route("/todos/<int:todo_id>", methods=["GET"])
def get_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({"error":"Todo not found"}), 404 # return type is (JSONIFY error, status_code)
    return jsonify(todo.to_dict())

### Creating a todo
@api.route("/todos", methods=["POST"])
def create_todo():
    todo = Todo(
        title=request.json.get("title"),
        description=request.json.get("description"),
        completed=request.json.get("completed", False)
    )
    if "deadline_at" in request.json:
        todo.deadline_at = datetime.fromisoformat(request.json.get("deadline_at"))

    # todo object completed here
    # add todo to SQLLite ORM 
    db.session.add(todo)
    # commit to save changes to the file
    db.session.commit()
    return jsonify(todo.to_dict()), 201

@api.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    """Update a todo item and return the updated item"""
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({"error","Todo not found"}), 404

    todo.title = request.json.get('title', todo.title)
    todo.description = request.json.get('description', todo.description)
    if str_to_bool(request.json.get('completed')) is not None:
        todo.completed = str_to_bool(request.json.get('completed'))
    
    if request.json.get('deadline_at'):
        todo.deadline_at = datetime.fromisoformat(request.json.get('deadline_at'))
    
    # Commit changes to DB to save changes to file
    db.session.commit()

    return jsonify(todo.to_dict())


@api.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    """Delete a todo item and return the deleted item"""
    # get todo
    todo = Todo.query.get(todo_id)

    # check if none, return error
    if todo is None:
        return jsonify({}), 400


    # delete from session and commit
    db.session.delete(todo)
    db.session.commit()

    # return todo
    return jsonify(todo.to_dict()), 200
 
