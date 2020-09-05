FROM python:3.8-alpine

COPY dev-cert.pem requirements.txt setup.py README.md /src/
COPY xman/* /src/xman/
WORKDIR /src
RUN ls -al
RUN pip install -r requirements.txt && python setup.py develop

ENTRYPOINT ["python", "-u", "-m", "xman"]
