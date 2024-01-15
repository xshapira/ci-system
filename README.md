# orca-ci-system-hiring-exercise

## Step Runner

A go program that simulates a build server for the exercise. To run it, you can:

### Usage

* Run the docker (Recommended): Run `docker build -t orca-ci-system-hiring-exercise . && docker run -it -p 8080:8080 orca-ci-system-hiring-exercise`
* Run locally: Run `go run main.go` in the root directory of this project.

You can control the server address with the `ORCA_STEP_RUNNER_SERVER_ADDR`
environment variable, by default it will be `:8080`.

### API documentation

How to use it? The server has a single endpoint, here's an example:

```bash
# Test the POST endpoint
curl -X POST http://localhost:8080/step/trigger \
     -H 'Content-Type: application/json' \
     -d '{
           "step_name": "lint",
           "repo_path": "/some/path/to/repo",
           "commit_hash": "1234567890"
         }'
```

There can be three steps in `step_name`: `lint`, `build`, and `test`.

* The `lint` step will always succeed and can run in parallel.
* The `build` step might succeed and might fail, and can't run in parallel with
  other builds.
* The `test` step might succeed and might fail, can't run in parallel with other
  tests, and MIGHT crash the server.

### Notes

The server is unstable - that is on purpose to simulate the realities of working
with a real CI pipeline that sometimes fails and sometimes crashes!

There isn't more documentation about the step runner. Review the code in main.go
if you want to know more.

## CI Server

Buggy Barry and Crash Carla started writing a CI server that watches a local git
repo and uses the step runner to run `lint`, `build`, and `test` on every
commit... But they left it with bad code and it's unfinished.

To run the CI server, run the following command:

```bash
poetry install
poetry run python ci_server.py
```

If you're having issues with `poetry` you can use `pip` instead:

```bash
pip install -r requirements.txt
python ci_server.py
```

