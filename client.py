# import csv
import grpc
import modelserver_pb2
import modelserver_pb2_grpc
import threading
import sys

stats_lock = threading.Lock()

def task(stub, idx, filename, stats):
    # print(stats, filename, idx)
    with open(filename, 'r') as fp:
        hit_count = 0
        total_count = 0
        for line in fp:
            X = list(map(float, line.split(",")))
            # print(X)
            total_count += 1
            resp = stub.Predict(modelserver_pb2.PredictRequest(X=X))
            hit = resp.hit
            if hit:
                hit_count += 1
    with stats_lock:
        stats[idx] = (hit_count, total_count)
        # print(stats[idx])

def main(args):
    # print(args)
    port = args[0]
    coefs = list(map(float, args[1].split(",")))
    thread_count = len(args) - 2

    channel = grpc.insecure_channel("localhost:" + str(port))
    stub = modelserver_pb2_grpc.ModelServerStub(channel)
    stub.SetCoefs(modelserver_pb2.SetCoefsRequest(coefs=coefs))

    threads = []
    stats = [None for _ in range(thread_count)]
    for idx in range(thread_count):
        filename = args[idx + 2]
        thread = threading.Thread(target=task, args=[stub, idx, filename, stats])
        thread.start()
        # thread.join()
        threads.append(thread)
    for _ in range(thread_count):
        threads[_].join()

    total_hits = 0
    total_lines = 0
    for _ in range(len(stats)):
        total_hits += stats[_][0]
        total_lines += stats[_][1]
    print(total_hits*1.0/total_lines)

if __name__ == "__main__":
    main(sys.argv[1:])

