import tempfile
import pathlib
import uuid
import pytest

from tests.resources.helper_functions import get_publisher_instance

pytestmark = pytest.mark.skip(reason="Requires Powergate in the CI")

def test_upload_filecoin():
    publisher_instance = get_publisher_instance(True, False, False)

    with tempfile.NamedTemporaryFile() as f:
        f.write(b"Hello, Nevermined!")
        f.flush()
        url = publisher_instance.files.upload_filecoin(f.name)

    assert url == "cid://QmSJA3xNH62sj4xggZZzCp2VXpsXbkR9zYoqNYXp3c4xuN"


def test_create_asset_with_cid(metadata):
    publisher_instance = get_publisher_instance(True, False, False)
    publisher = publisher_instance.main_account

    with tempfile.NamedTemporaryFile() as f:
        f.write(b"aaa")
        f.flush()
        url = publisher_instance.files.upload_filecoin(f.name)

    metadata["main"]["files"] = [
        {
            "index": 0,
            "contentType": "text/text",
            "encoding": "UTF-8",
            "compression": "zip",
            "checksum": str(uuid.uuid4()),
            "checksumType": "MD5",
            "contentLength": "12057507",
            "url": url,
        }
    ]
    ddo = publisher_instance.assets.create(metadata, publisher)
    assert ddo is not None


def test_download_asset_with_cid(metadata):
    publisher_instance = get_publisher_instance(True, False, False)
    publisher = publisher_instance.main_account

    with tempfile.NamedTemporaryFile() as f:
        f.write(b"bbb")
        f.flush()
        url = publisher_instance.files.upload_filecoin(f.name)

    metadata["main"]["files"] = [
        {
            "index": 0,
            "contentType": "text/text",
            "encoding": "UTF-8",
            "compression": "zip",
            "checksum": str(uuid.uuid4()),
            "checksumType": "MD5",
            "contentLength": "12057507",
            "url": url,
        }
    ]
    ddo = publisher_instance.assets.create(metadata, publisher)

    service_agreement = ddo.get_service("access")
    path = publisher_instance.assets.download(
        ddo.did, service_agreement.index, publisher, "/tmp/outputs"
    )
    assert path is not None

    with (pathlib.Path(path) / "file-0").open("rb") as f:
        assert f.read() == b"bbb"
