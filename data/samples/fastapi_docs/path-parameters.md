# Path Parameters

Path parameters are the variable parts of the URL path itself, declared with
the same curly-brace syntax Python uses for format strings. They are always
required — a URL either contains that path segment or it doesn't match the
route at all.

## Declaring a path parameter

The parameter name in the path must match a function argument. Whatever the
client puts in that URL segment is passed to your function.

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/users/{user_id}")
def read_user(user_id: int):
    return {"user_id": user_id}
```

Because `user_id` is annotated as `int`, FastAPI parses and validates the
segment before calling the handler. `/users/42` gives you the integer `42`;
`/users/abc` never reaches your code — the client gets a 422 with a message
explaining that the value is not a valid integer. Typed path parameters give
you data validation for free.

## Route order matters

Routes are matched in declaration order. If you have a fixed path that could
also match a parameterized one, declare the fixed path first.

```python
@app.get("/users/me")
def read_current_user():
    return {"user": "the current user"}

@app.get("/users/{user_id}")
def read_user(user_id: int):
    return {"user_id": user_id}
```

Declared the other way around, `/users/me` would be captured by
`/users/{user_id}` and fail with a type error, because `"me"` is not an
integer. This bites people migrating from frameworks that match most-specific
first.

## Restricting values with enums

When a path parameter should only accept a fixed set of values, subclass
`str` and `Enum` and use that as the annotation. The docs UI then renders a
dropdown, and invalid values are rejected automatically.

```python
from enum import Enum

class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"

@app.get("/models/{model_name}")
def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep learning FTW"}
    return {"model_name": model_name}
```

## Paths containing slashes

A parameter declared as `{file_path:path}` matches the rest of the URL
including slashes, which is what you want for file-browser style endpoints
like `/files/{file_path:path}` receiving `/files/home/user/notes.txt`.
