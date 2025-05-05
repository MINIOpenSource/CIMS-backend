FROM python:3.13.2-alpine3.21
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir --root-user-action ignore -r requirements.txt \
    && find Protobuf/ -type f -name "*.proto" \
    | xargs python -m grpc_tools.protoc --proto_path=. --python_out=. --grpc_python_out=. \
    && echo '{"gRPC":{"prefix":"http","host":"localhost","port":50050},"api":{"prefix":"http","host":"localhost","port":50051},"command":{"prefix":"http","host":"localhost","port":50052},"organization_name":"CIMSDefaultOrganization"}' > settings.json \
    && touch .installed
CMD [ "python3", "CIMS.py" ]
