# api

This repository contains the public facing bitdrift APIs. The high level repository structure is
as follows:
  1. `thirdparty/` contains vendored protobuf files required for compilation.
  2. `src/` contains the actual APIs as implemented both by the client SDKs as well as any
      compliant control plane.

Currently we don't have any high level API documentation but will work on rectifying this in the
future. In the interim the actual proto files should be reasonably well documented and of course
the client SDK code is available for inspection to better understand what the clients send and
receive.

A limited set of bitdrift SaaS APIs are also defined in this repository. Over time this will be
expanded and substantially better documented.
