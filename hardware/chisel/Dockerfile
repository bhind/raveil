FROM --platform=linux/amd64 eclipse-temurin:17-jdk-jammy

ARG SCALA_CLI_VERSION=1.10.1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl g++ make perl perl-modules-5.34 verilator \
    && curl --fail --location --retry 3 \
       "https://github.com/VirtusLab/scala-cli/releases/download/v${SCALA_CLI_VERSION}/scala-cli-x86_64-pc-linux.gz" \
       --output /tmp/scala-cli.gz \
    && gzip -d /tmp/scala-cli.gz \
    && install -m 0755 /tmp/scala-cli /usr/local/bin/scala-cli \
    && rm -rf /var/lib/apt/lists/* /tmp/scala-cli

WORKDIR /work
COPY hardware/chisel/ /work/

CMD ["./run-smoke.sh"]
