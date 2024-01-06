FROM ubuntu:23.10
RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip3 install grpcio==1.58.0 grpcio-tools==1.58.0 --break-system-packages
RUN pip3 install torch==2.0.1 --index-url https://download.pytorch.org/whl/cpu --break-system-packages
RUN pip3 install tensorboard==2.14.0 --break-system-packages
CMD ["python3", "-m", "grpc_tools.protoc", "-I=.", "--python_out=.", "--grpc_python_out=.", "modelserver.proto"]

RUN mkdir /app
RUN touch /app/output.txt
COPY *.py /app/
CMD ["python3", "/app/server.py", ">", "/app/output.txt"]
