FROM python:slim

RUN apt-get update && apt-get install -y socat
RUN pip install -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple pycryptodome

COPY arcahv.py /app/
RUN chmod 755 /app/
RUN echo $FLAG > /app/flag.txt
WORKDIR /app/
EXPOSE 8000
CMD ["socat", "TCP-LISTEN:8000,reuseaddr,fork", "EXEC:'python3 arcahv.py',pty,stderr,echo=0"]