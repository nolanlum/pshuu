import os
import types

import pytest

from files import FileMapper


@pytest.mark.parametrize("number", [1, 61, 62, 63, 12345, 0xFFFFFFFF])
def test_b62_roundtrip(number):
    assert FileMapper.b62_decode(FileMapper.b62_encode(number)) == number


def test_b62_encode_zero_is_empty_and_decodes_back():
    assert FileMapper.b62_encode(0) == ""
    assert FileMapper.b62_decode("") == 0


def test_b62_decode_invalid_raises_value_error():
    with pytest.raises(ValueError):
        FileMapper.b62_decode("!!!")


def _user(username="alice"):
    return types.SimpleNamespace(username=username)


def test_get_file_key_deterministic_and_length():
    m = FileMapper(_user("alice"))
    k1 = m.get_file_key(42)
    k2 = m.get_file_key(42)
    assert k1 == k2
    assert len(k1) == FileMapper.FILE_KEY_LENGTH


def test_get_file_key_depends_on_username_and_id():
    assert FileMapper(_user("alice")).get_file_key(42) != FileMapper(
        _user("bob")
    ).get_file_key(42)
    m = FileMapper(_user("alice"))
    assert m.get_file_key(42) != m.get_file_key(43)


def test_get_delete_key_deterministic_and_length():
    k1 = FileMapper.get_delete_key(42)
    assert k1 == FileMapper.get_delete_key(42)
    assert k1 != FileMapper.get_delete_key(43)
    assert len(k1) == FileMapper.DELETE_KEY_LENGTH


def test_storage_and_thumb_path_format(app):
    # 0x12345 -> "00012345" -> <dir> / 00 / 012 / 345
    assert FileMapper.get_storage_path(0x12345) == os.path.join(
        app.config["UPLOAD_DIRECTORY"], "00", "012", "345"
    )
    assert FileMapper.get_thumb_path(0x12345) == os.path.join(
        app.config["THUMBS_DIRECTORY"], "00", "012", "345"
    )
