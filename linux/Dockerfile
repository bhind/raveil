ARG BASE_IMAGE=debian:bookworm-slim
FROM ${BASE_IMAGE}
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libc6-dev make \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /raveil
COPY linux /raveil/linux
COPY contracts /raveil/contracts
WORKDIR /raveil/linux
RUN make clean && make all contracts-check
CMD ["make", "smoke"]
