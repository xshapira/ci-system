# CI Server

## Step Runner

A go program that simulates a build server. To run it, you can:

* Run with docker (Recommended):

```docker
  docker build -t ci-server . && docker run -it -p 8080:8080 ci-server
  ```

* Run locally in the root directory of this project:

```go
  go run main.go
  ```

You can control the server address with the `STEP_RUNNER_SERVER_ADDR` environment variable, by default it will be `:8080` .

### API documentation

How to use it? The server has a single endpoint, here's an example:

```bash
# Test the POST endpoint
curl -X POST http://localhost:8080/step/trigger \
     -H 'Content-Type: application/json' \
     -d '{
           "step_name": "lint",
           "repo_path": "/some/path/to/local/repo",
           "commit_hash": "1234567890"
         }'
```

There can be three steps in `step_name` : `lint` , `build` , and `test` .

* The `lint` step will always succeed and can run in parallel.
* The `build` step might succeed and might fail, and can't run in parallel with
  other builds.
* The `test` step might succeed and might fail, can't run in parallel with other
  tests, and MIGHT crash the server.

### Notes

The server is *intentionally* **unstable** to simulate the real experience of working with a CI pipeline that may occasionally fail or crash.

## CI Server

The CI server watches a local git
repo and uses the step runner to run `lint` , `build` , and `test` on every
commit.

To run the CI server, run the following command:

```bash
poetry install
poetry run python ci_server.py "/some/path/to/local/repo" ":8080"
```
