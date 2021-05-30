set -x

# installing homebrew

bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# install cdk dependencies
brew install npm
npm install -g aws-cdk

# install openssl https://stackoverflow.com/a/56228387/5933618
# prevents potential python installation errors

brew install openssl
export LDFLAGS="-L/usr/local/opt/openssl/lib"
export CPPFLAGS="-I/usr/local/opt/openssl/include"

# install pipx (for installing python cli's)

brew install pipx
brew upgrade pipx

pipx --upgrade-all

# installing pyenv

curl https://pyenv.run | bash
~/.pyenv/bin/pyenv update

# install python

~/.pyenv/bin/pyenv install $PYTHON_VERSION

# create virtualenv

rm -rf .venv
~/.pyenv/versions/$PYTHON_VERSION/bin/python -m venv .venv

# configure pdm

pdm config -l python.path .venv/bin/python
pdm config -l use_venv true

# install app library dependencies

pdm install -s :all

# install git hooks

pdm run pre-commit install --install-hooks

# list development commands

pdm run -l
