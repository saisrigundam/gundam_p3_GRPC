# Sai Sri Gundam

import grpc
import modelserver_pb2_grpc
import modelserver_pb2
import threading
import torch

from concurrent import futures

class PredictionCache:
    def __init__(self):
        self.coefs = []
        self.cache = {}
        self.cache_size = 10
        self.evict_order = []
        self.lock = threading.Lock()

    def SetCoefs(self, coefs):
        with self.lock:
            self.coefs = coefs
            self.evict_order.clear()
            self.cache.clear()

    def Predict(self, X):
        print("Predict: ", X.flatten().tolist())
        print("Cache")
        print(self.cache)
        print("----------------------")
        X = torch.round(X, decimals=4)
        X_tuple = tuple(X.flatten().tolist())
        with self.lock:
            isHit = X_tuple in self.cache
            if isHit:
                self.evict_order.remove(X_tuple)
                self.evict_order.append(X_tuple)
                return self.cache[X_tuple], True
            else:
                y_predict = X @ self.coefs
                print("Predicted:", y_predict.item())
                self.cache[X_tuple] = y_predict.item()
                # print(1)
                self.evict_order.append(X_tuple)
                # print(2)
                if len(self.cache) > self.cache_size:
                    # print(3)
                    print(self.evict_order)
                    evict_key = self.evict_order.pop(0)
                    print(evict_key)
                    evict_value = self.cache.pop(evict_key)
                    print(5)
                print("Cache final: ", self.cache)
                print("Predicted final: ", y_predict.item())
                return y_predict.item(), False


class ModelServer(modelserver_pb2_grpc.ModelServerServicer):
    def __init__(self):
        self.cache = PredictionCache()
        # self.lock = threading.Lock()

    def SetCoefs(self, request, context):
        # print("11111")
        try:
            coefs_tensor = torch.tensor(request.coefs, dtype=torch.float32)
            # print("coef_tensor_size:", coefs_tensor.size())
            # with self.lock:
            self.cache.SetCoefs(coefs_tensor)
            return modelserver_pb2.SetCoefsResponse(error="")
        except Exception as e:
            # print("Error", e)
            return modelserver_pb2.SetCoefsResponse(error=str(e))

    def Predict(self, request, context):
        # print("22222")
        try:
            x_tensor = torch.tensor(request.X, dtype=torch.float32)
            # print("x_tensor_size before:", x_tensor.size())
            x_tensor = x_tensor.view(-1)
            # x_tensor = torch.flatten(x_tensor)
            # print("x_tensor_size after:", x_tensor.size())
            # with self.lock:
            y_predict, cache_hit = self.cache.Predict(x_tensor)
            print(x_tensor, y_predict)
            return modelserver_pb2.PredictResponse(y=y_predict, hit=cache_hit, error="")
        except Exception as e:
            # print("error: ", e)
            return modelserver_pb2.PredictResponse(y=0.0, hit=False, error=str(e))

def main():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4), options=(('grpc.so_reuseport', 0),))
    modelserver_pb2_grpc.add_ModelServerServicer_to_server(ModelServer(), server)
    server.add_insecure_port("[::]:5440", )
    server.start()
    # print("Started")
    server.wait_for_termination()


if __name__ == "__main__":
    main()


