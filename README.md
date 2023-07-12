# MyCITool

A tool that checks out a GitHub repository, verifies a Dockerfile exists, builds the Docker container described in said Dockerfile, runs the resulting Docker image, and verifies that the container is running.

A watcher Bash script is included

## Requirements:

* Docker daemon running in the background
* Python 3.7 or newer
* Git 1.70 or newer
* GitPython

## Running the tool
```
python3 mycitool.py [GitHub URL] [local path to clone the repo to]
```

Example:

```
python3 mycitool.py https://github.com/yaariyuval/outbrain-cherrypy /tmp/outbrain-cherrypy
```

### Optional arguments:
| Argument      | Description   | Default value |
| ------------- |---------------|---------------|
| -b, --branch  | Specify which branch to check out | main |
| -t, --timeout | Specify timeout when waiting for container to reach the 'running' state, in seconds | 120 |
| --tag         | Specify a tag to apply to the Docker container being built | outbrain-cherrypy |


```
$ crontab -e
```

And add

```
* * * * * /path/to/watcher.sh
```

In order to run the watcher script every minute
