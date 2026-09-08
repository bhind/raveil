FROM ubuntu@sha256:1e0a86e57d247923571b75e0aaf48a1449cf8c543d51fb3e07a4a7d7bfa79316 AS dependencies

ARG UBUNTU_SNAPSHOT=20260908T000000Z
ENV DEBIAN_FRONTEND=noninteractive

# Bootstrap TLS with an exact package version, then resolve every remaining
# package from one signed Ubuntu archive snapshot.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates=20260601~24.04.1 \
    && rm -rf /var/lib/apt/lists/*
RUN apt-get update --snapshot "${UBUNTU_SNAPSHOT}" \
    && apt-get install -y --no-install-recommends \
        autoconf automake build-essential cmake git graphviz latex2html \
        libboost-all-dev libedit-dev libffi-dev libsqlite3-dev libtool \
        libwxgtk3.2-dev libxerces-c-dev make sqlite3 subversion tcl8.6-dev \
    && dpkg-query -W -f='${binary:Package}\t${Version}\n' | sort > /opt/ubuntu-packages.tsv \
    && rm -rf /var/lib/apt/lists/*

FROM dependencies AS sources

ARG OPENASIP_REVISION=f2282048f4c78d18190a9b77e7497e29a164721d
ARG LLVM_REVISION=b47e651cc052ba9e097701efa8840e8f3081c84d
RUN git init /opt/src/openasip \
    && git -C /opt/src/openasip remote add origin https://github.com/cpc/openasip.git \
    && git -C /opt/src/openasip fetch --depth=1 origin "${OPENASIP_REVISION}" \
    && git -C /opt/src/openasip checkout --detach FETCH_HEAD \
    && test "$(git -C /opt/src/openasip rev-parse HEAD)" = "${OPENASIP_REVISION}" \
    && git -C /opt/src/openasip status --porcelain | test ! -s /dev/stdin
RUN git init /opt/src/llvm \
    && git -C /opt/src/llvm remote add origin https://github.com/cpc/llvmtce.git \
    && git -C /opt/src/llvm fetch --depth=1 origin "${LLVM_REVISION}" \
    && git -C /opt/src/llvm checkout --detach FETCH_HEAD \
    && test "$(git -C /opt/src/llvm rev-parse HEAD)" = "${LLVM_REVISION}" \
    && git -C /opt/src/llvm status --porcelain | test ! -s /dev/stdin

FROM sources AS toolchain

ENV PATH=/opt/openasip/bin:${PATH}
ENV LD_LIBRARY_PATH=/opt/openasip/lib
ENV LDFLAGS=-L/opt/openasip/lib
RUN cmake -S /opt/src/llvm/llvm -B /opt/src/llvm/build \
        -G 'Unix Makefiles' \
        -DCMAKE_BUILD_TYPE=Release \
        -DLLVM_ENABLE_ASSERTIONS=ON \
        -DCMAKE_INSTALL_PREFIX=/opt/openasip \
        -DLLVM_ENABLE_PROJECTS='clang;lld' \
        -DLLVM_TARGETS_TO_BUILD=X86 \
        -DLLVM_LINK_LLVM_DYLIB=TRUE \
        -DLLVM_ENABLE_RTTI=TRUE \
        -DLLVM_ENABLE_Z3_SOLVER=OFF \
    && cmake --build /opt/src/llvm/build --parallel 4 \
    && cmake --install /opt/src/llvm/build
RUN cd /opt/src/openasip/openasip \
    && ./autogen.sh \
    && ./configure --prefix=/opt/openasip \
    && make -j4 \
    && make install \
    && ttasim --version
ENV HOME=/opt/openasip-home
COPY programs/reduction.c /opt/t0191-plugin-prewarm.c
RUN mkdir -p "${HOME}" \
    && oacc -O3 \
        -a /opt/openasip/share/openasip/data/mach/minimal.adf \
        -o /opt/t0191-plugin-prewarm.tpef \
        -k main,result /opt/t0191-plugin-prewarm.c \
    && test -s /opt/t0191-plugin-prewarm.tpef \
    && find "${HOME}/.cache/openasip/tcecc" -type f -name '*.so*' -size +0c | grep -q . \
    && rm /opt/t0191-plugin-prewarm.c /opt/t0191-plugin-prewarm.tpef \
    && chmod -R a-w "${HOME}"
