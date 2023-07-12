import argparse
import os, shutil
import sys
from time import sleep 
import logging
import traceback

import docker
import git

logging.basicConfig(level=logging.INFO)
client = docker.from_env()

def checkout_repo(repo_url, repo_path, repo_branch):
    # Check if the directory we want to clone the Git repo into already exists, and delete it if it does
    if os.path.isdir(repo_path):
        shutil.rmtree(repo_path)

    repo = git.Repo.clone_from(repo_url, repo_path, branch=repo_branch)
    logging.info(f"Repository {repo_url} checked out to {repo_path}")

def build_image(repo_dir, image_tag):
    if not os.path.isfile(repo_dir + "/Dockerfile"):
        logging.error("Dockerfile not found in Git repository")
        raise Exception("Dockerfile not found in Git repository")

    logging.info("Building Docker image")
    try:
        image, logs = client.images.build(path=repo_dir, tag=image_tag)
    except BuildError as e:
        logging.error("Failed to build docker image")
        raise e
    except TypeError as e:
        logging.error("You must provide a path to the build environemnt.")
        raise e
    except APIError as e:
        logging.error("Docker server error while building image")
        raise e
    else:
        logging.info(f"Image built: {image.short_id}")

def run_container(image_tag, timeout):
    logging.info("Checking if the container is already running")
    try:
        running_container = client.containers.get(image_tag)
    except docker.errors.NotFound:
        logging.info("Container isn't already running")
    else:
        logging.info("Container is already running, stopping and removing it first")
        try:
            running_container.stop()
            running_container.remove()
        except APIError:
            logging.error("Docker daemon returned an API Error while trying to stop the container")
            logging.exception(e)
            raise e

    logging.info("Running Docker image")
    try:
        container = client.containers.run(
            image=image_tag,
            name=image_tag,
            ports={'8080/tcp': 8080},
            detach=True
        )
    except APIError as e:
        logging.error("Docker daemon returned an API Error while trying to run the container")
        logging.exception(e)
        raise e
    except Exception as e:
        logging.exception(e)
        raise e

    logging.info(f"Container created: {container.short_id}")
    logging.info(f"Waiting for container to run")

    # Wait until the container is actually running
    # Sleep for 1 second between checks
    # Timeout after `timeout` seconds (120 seconds by default; configurable via command line)
    # Please note that contain.status will remain 'created', and we need to query the Docker client
    # to check whether the container is actually running
    sleep_time = 1
    elapsed_time = 0
    status = client.containers.get(container.id).status
    while status != 'running' and elapsed_time < timeout:
        sleep(sleep_time)
        elapsed_time += sleep_time
        status = client.containers.get(container.id).status
        continue

    if status != 'running':
        logging.error(f"Container failed to start: {container.short_id}")
        raise Exception("Container failed to start")
    else: 
        logging.info(f"Container created: {container.short_id}")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", help="The URL for the Git repository to clone")
    parser.add_argument("path", help="The local path to clone the Git repository into")
    parser.add_argument("-b", "--branch", default="main",
                    help="Specify which branch to check out (Optional, defaults to main)")
    parser.add_argument("-t", "--timeout", default=120, type=int,
                    help="Specify timeout when waiting for container to reach the 'running' state, in seconds (optional, defaults to 120 seconds)")
    parser.add_argument("--tag", default="outbrain-cherrypy",
                    help="Specify a tag to apply to the Docker container being built (optional, defaults to 'outbrain-cherrypy')")
    args = parser.parse_args()

    repo_url = args.repo
    repo_path = args.path
    repo_branch = args.branch
    timeout = args.timeout
    image_tag = args.tag

    # Clone the Git repo specified in the command line arguments
    checkout_repo(repo_url, repo_path, repo_branch)

    # Build the Docker image
    build_image(repo_path, image_tag)

    # Run the Docker image
    run_container(image_tag, timeout)
