FROM raveil-sonatine:gate0-clean-20260808
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libc6-dev make \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /raveil
COPY . /raveil
RUN make clean && make
CMD ["make", "smoke"]
