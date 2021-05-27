## Expectations

You will need the following installed on your machine for development:

* A Python 3.8 interpreter
* @pdm-project/pdm (for managing the project and task automation)
* @nodejs/nodejs.dev (for the AWS CDK)

### Quickstart

#### Mac Users

!!! note

    It's recommended you read the ==scripts/bootstrap.sh== script that's invoked by the `Makefile`

```bash
make
```

!!! question "What just happened when I ran make?"

- @Homebrew/brew (a MacOS package manager) was installed
- @pyenv/pyenv was installed for installing python
- @pipxproject/pipx was installed for python command-line utilities
- @pdm-project/pdm was installed for dependency management and project automation
- A python3.8 virtual environment was created at in `.venv`
- pdm installed our project's python library dependencies
- The project's git hooks were installed
