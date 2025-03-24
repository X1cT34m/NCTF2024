FROM ubuntu:22.04

RUN apt-get update && apt-get install -y python3-pip python3-dev ncat cron

RUN pip3 install pyfiglet

WORKDIR /app

COPY task.py /app/

RUN echo "#!/bin/bash\n\npython3 -u task.py 2>&1" > ./wrapper.sh

RUN chmod -R 555 /app

CMD cron && ncat -klvp 2222 -m 999999 -e ./wrapper.sh
