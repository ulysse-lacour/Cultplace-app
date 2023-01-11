import json
from datetime import date

import pytest
from project.models.abstract import SerializableModel
from utils.errors.http_errors import SerializationError


def test_serializable_model_serialize_success():
    my_model = SerializableModel(
        integer=1,
        string="I am a string",
        float_value=1.2,
        dict_value={
            "foo": "bar",
            50: "bar"
        },
        list_value=[
            "foo",
            1,
            1.1,
            True
        ],
        boolean_value=True,
        date_value=date.today(),
        none_value=None,
        __implicit_private_field="I must not be serialized",
        declared_private_field="someone specifically told to not serialize me"
    )

    type(my_model).non_serializable_fields = {"declared_private_field"}

    result = my_model.serialize()

    assert isinstance(result, str)

    dict_result = json.loads(result)
    expected_dict_result = {
        "integer": 1,
        "string": "I am a string",
        "float_value": 1.2,
        "dict_value": {
            "foo": "bar",
            "50": "bar"
        },
        "list_value": [
            "foo",
            1,
            1.1,
            True
        ],
        "date_value": str(date.today()),
        "boolean_value": True,
        "none_value": None,
    }

    assert "__private_field" not in dict_result.keys()
    assert "declared_private_field" not in dict_result.keys()

    assert expected_dict_result == dict_result


def test_serializable_model_serialize_success_with_arguments():
    my_model = SerializableModel(
        foo="bar"
    )

    result = my_model.serialize(
        "first_argument",
        1,
        1.2,
        my_keyword_argument="a keyword argument"
    )

    dict_result = json.loads(result)
    expected_dict_result = {
        "foo": "bar",
        "my_keyword_argument": "a keyword argument",
        "args_list": [
            "first_argument",
            1,
            1.2,
        ],
    }

    assert expected_dict_result == dict_result


# def test_serializable_model_serialize_error_unserializable_field():
# FIXME : This error will never occurs, need to find a non value that cannot convert to string
#     class MyFakeModelClass(SerializableModel):
#         ...

#     my_model = MyFakeModelClass(
#         id=12345,
#         unserializable_object={"hi, there", "im", "a", "set"}
#     )

#     with pytest.raises(SerializationError) as excinfo:
#         my_model.serialize()

#     assert excinfo.value.code == 422
#     assert excinfo.value.description == "Error serializing a model to JSON"
#     assert excinfo.value.extra.get("model_name") == "MyFakeModelClass"
#     assert excinfo.value.extra.get("model_id") == my_model.id
