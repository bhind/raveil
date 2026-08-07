FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       gcc-riscv64-unknown-elf \
       make \
       qemu-system-misc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /raveil/sonatine
COPY . .
RUN make

CMD ["make", "run"]
