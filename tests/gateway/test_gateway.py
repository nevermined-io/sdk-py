from nevermined_sdk_py import ConfigProvider
from nevermined_sdk_py.gateway.gateway import Gateway
from requests import Response

config = ConfigProvider.get_config()


def test_get_rsa_key():
    assert Gateway.get_rsa_public_key(config)


def test_get_file_name():
    response = Response()

    response.headers = {"content-disposition": "attachment;filename=test.txt"}
    print(response.headers.get("content-disposition"))
    file_name = Gateway._get_file_name(response)
    assert file_name == "test.txt"

    response.headers = {
        "content-disposition": "attachment;filename=test.txt?X-Amz-Algorithm=AWS4-HMAC-SHA256"
    }
    file_name = Gateway._get_file_name(response)
    assert file_name == "test.txt"
