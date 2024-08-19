FROM cimg/python:3.10.12-node

USER root

# Install dependencies and Go
RUN apt-get update && \
    apt-get install -y wget && \
    wget https://go.dev/dl/go1.22.5.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.22.5.linux-amd64.tar.gz && \
    rm go1.22.5.linux-amd64.tar.gz

# Set Go environment variables
ENV PATH="/root/.local/bin:/usr/local/go/bin:${PATH}"

# Verify installations
RUN python --version && go version

RUN curl -L https://foundry.paradigm.xyz | bash
RUN source ~/.bashrc
ENV PATH="/root/.foundry/bin:${PATH}"
RUN foundryup

USER $USERNAME
