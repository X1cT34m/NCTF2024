FROM rust:1.85 AS builder

RUN mkdir -vp ${CARGO_HOME:-$HOME/.cargo}

RUN cat <<EOF | tee -a ${CARGO_HOME:-$HOME/.cargo}/config.toml
[source.crates-io]
replace-with = 'ustc'

[source.ustc]
registry = "sparse+https://mirrors.ustc.edu.cn/crates.io-index/"
EOF

COPY ./internal_api/ /build/

WORKDIR /build/

RUN cargo build --release

FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources && \
    apt update && \
    apt install -y sqlite3 openssl

COPY --from=builder /build/target/release/internal_api /app/internal_api
COPY --from=builder /build/comments.json /app/comments.json

WORKDIR /app/

ENV HOST=0.0.0.0
ENV PORT=8000
ENV DB_NAME=file.db
ENV JSON_NAME=comments.json

CMD ["./internal_api"]
