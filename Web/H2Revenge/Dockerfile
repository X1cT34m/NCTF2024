FROM eclipse-temurin:17-jre

RUN groupadd -r ctf && \
    useradd -m -r -g ctf ctf && \
    mkdir /app/ && \
    chown -R ctf:ctf /app/

COPY --chmod=755 ./files/docker-entrypoint.sh /
COPY ./files/H2Revenge.jar /app/

ENTRYPOINT [ "/docker-entrypoint.sh" ]