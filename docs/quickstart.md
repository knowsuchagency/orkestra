There exists a minimal and slightly opinionated [starter template](https://github.com/knowsuchagency/orkestra_template/tree/main/project)
to help you get started.

## Pre-requisites

* [copier](https://copier.readthedocs.io/en/latest/)
* [pdm](https://pdm.fming.dev)
* [cdk cli](https://docs.aws.amazon.com/cdk/latest/guide/cli.html)


## Usage

```bash

# install dependencies

brew install pipx
brew install npm # (if not installed)

npm install -g aw-cdk

pipx install copier
pipx install pdm

# render the template

copier gh:knowsuchagency/orkestra_template destination_directory
```

You can now follow along with the instructions in the project readme.
