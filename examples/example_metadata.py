#  Copyright 2018 Nevermined Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0
import uuid

metadata = {
    "main": {
        "name": "Nevermined protocol white paper",
        "dateCreated": "2012-02-01T10:55:11Z",
        "author": "Mario",
        "license": "CC0: Public Domain",
        "price": "0",
        "files": [
            {
                "index": 0,
                "contentType": "text/text",
                "checksum": str(uuid.uuid4()),
                "checksumType": "MD5",
                "contentLength": "12057507",
                "url": "https://raw.githubusercontent.com/keyko-io/nevermined-tools/master/README.md"
            }
        ],
        "type": "dataset"
    }
}

algo_metadata = {
        "main": {
          "author": "John Doe",
          "checksum": "0x52b5c93b82dd9e7ecc3d9fdf4755f7f69a54484941897dc517b4adfe3bbc3377",
          "dateCreated": "2019-02-08T08:13:49Z",
          "license": "CC-BY",
          "name": "My workflow",
          "price": "1",
          "files": [
              {
                  "index": 0,
                  "contentType": "text/text",
                  "checksum": str(uuid.uuid4()),
                  "checksumType": "MD5",
                  "contentLength": "12057507",
                  "url": "https://raw.githubusercontent.com/keyko-io/nevermined-tools/master/README.md"
              }
          ],
          "type": "algorithm",
          "algorithm": {
            "language": "python",
            "format": "py",
            "version": "0.1",
            "entrypoint": "python word_count.py",
            "requirements": [
              {
                "container": {
                    "image": "python",
                    "tag": "3.8-alpine",
                    "checksum":"sha256:53ad3a03b2fb240b6c494339821e6638cd44c989bcf26ec4d51a6a52f7518c1d"
                }
              }
            ]
          }
        }
}

compute_ddo = {
  "main": {
    "name": "10 Monkey Species Small",
    "dateCreated": "2012-02-01T10:55:11Z",
    "author": "Mario",
    "license": "CC0: Public Domain",
    "price": "10",
    "type": "compute"
  }
}

workflow_ddo = {
    "main": {
    "author": "John Doe",
    "checksum": "0x52b5c93b82dd9e7ecc3d9fdf4755f7f69a54484941897dc517b4adfe3bbc3377",
    "dateCreated": "2019-02-08T08:13:49Z",
    "datePublished": "2019-05-08T08:13:49Z",
    "license": "CC-BY",
    "name": "My workflow",
    "price": "1",
    "type": "workflow",
    "workflow": {
        "stages": [
            {
                "index": 0,
                "stageType": "Filtering",
                "requirements": {
                    "container": {
                        "image": "openjdk",
                        "tag": "14-jdl",
                        "checksum":"sha256:53ad3a03b2fb240b6c494339821e6638cd44c989bcf26ec4d51a6a52f7518c1d"
                    }
                },
                "input": [
                    {
                        "index": 0,
                        "id": "did:nv:12345"
                    },
                    {
                        "index": 1,
                        "id": "did:nv:67890"
                    }
                ],
                "transformation": {
                    "id": "did:nv:abcde"
                },
                "output": {
                    "metadataUrl": "https://localhost:5000/api/v1/metadata/assets/ddo/",
                    "secretStoreUrl": "http://localhost:12001",
                    "accessProxyUrl": "https://localhost:8030/api/v1/gateway/",
                    "metadata": {}
                }
            }
        ]
    }
}
}
