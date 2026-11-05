FROM ubuntu:24.04@sha256:561618e2c15bf2397621dd04f96926663a3b5616c189cf7e38db7e82f5c538ea
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    g++ make cmake ninja-build python3 verilator iverilog yosys clang-format \
    libssl-dev zlib1g-dev ca-certificates \
    && rm -rf /var/lib/apt/lists/*
ARG BUILD_UID=1000
ARG BUILD_GID=1000
RUN if ! getent group ${BUILD_GID} >/dev/null; then groupadd -g ${BUILD_GID} build; fi \
    && if ! getent passwd ${BUILD_UID} >/dev/null; then useradd -m -u ${BUILD_UID} -g ${BUILD_GID} build; fi
USER ${BUILD_UID}:${BUILD_GID}
WORKDIR /build
