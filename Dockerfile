FROM python:3.10 as pdm-builder
WORKDIR /root
RUN uname -a
RUN env
RUN curl -sSL https://raw.githubusercontent.com/pdm-project/pdm/main/install-pdm.py > install-pdm.py
RUN python3 install-pdm.py -p /root/.pdm
ENV PATH="/root/.pdm/bin:${PATH}"
WORKDIR /app
ADD README.md pdm.lock pyproject.toml /app/
RUN pdm install


# compile account-abstraction and bundler-tests to folders under "/out"
FROM node:20 as artifacts
WORKDIR /build
RUN git clone https://github.com/eth-infinitism/bundler-spec -b main #releases/v0.7
RUN cd bundler-spec && yarn remove gatsby ; yarn && yarn build && rm -rf node_modules
RUN git clone https://github.com/eth-infinitism/account-abstraction.git -b releases/v0.7
RUN cd account-abstraction && yarn && yarn compile
RUN mkdir -p /out/@account-abstraction /out/spec
RUN cd account-abstraction && mv contracts artifacts /out/@account-abstraction
#RUN cp `find /bundler-spec/* -maxdepth 0 -type f` /out/spec/ 
RUN cp bundler-spec/openrpc.json /out/spec


FROM python:3.10
WORKDIR /app
COPY --from=artifacts /out/ app
COPY --from=pdm-builder /root/.pdm /root/.pdm
COPY --from=pdm-builder /app /app
ENV PATH="/root/.pdm/bin:${PATH}"

#-v ./tests /app/tests
CMD  [ "bash" ]
