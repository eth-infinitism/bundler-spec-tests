FROM python:3.10
WORKDIR /app
RUN uname -a
RUN env
RUN curl -sSL https://raw.githubusercontent.com/pdm-project/pdm/main/install-pdm.py > install-pdm.py
RUN python3 install-pdm.py -p /usr/local/
ADD README.md pdm.lock pyproject.toml /app/
RUN curl -fsSL https://deb.nodesource.com/setup_16.x |  bash -
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - 
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list 
RUN apt update && apt install -y nodejs yarn
RUN pdm install

ADD .gitmodules /app/
ADD .git/ /app/.git
RUN pdm run update-deps
COPY tests/ /app/tests/
CMD  [ "/bin/sh", "-c", "echo \"run with 'pdm run test'\""  ]
