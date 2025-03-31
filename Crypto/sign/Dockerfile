FROM python:slim

RUN apt-get update && apt-get install -y socat
RUN pip install -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple pycryptodome

COPY srv.py /app/
COPY util.py /app/
RUN chmod 755 /app/
RUN echo 暗香疏影 > /app/secret.txt
WORKDIR /app/
EXPOSE 8000
CMD ["socat", "TCP-LISTEN:8000,reuseaddr,fork", "EXEC:'python3 srv.py',pty,stderr,echo=0"]