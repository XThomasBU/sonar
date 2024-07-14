import grpc
import comm_pb2
import comm_pb2_grpc
import threading
import time
from concurrent import futures
import gc
from typing import List, OrderedDict as OrderedDictType
from collections import OrderedDict
import numpy as np
import torch
import sys
import os

BASE_DIR = "/projectnb/ds598/projects/xthomas/temp/sonar"
sys.path.append(f"{BASE_DIR}/src/")

from utils.model_utils import ModelUtils
from torch.utils.data import DataLoader, Subset
from utils.data_utils import get_dataset
from utils.log_utils import LogUtils
from grpc_utils import deserialize_model, serialize_model


class Constants:
    def __init__(self):
        self.STATUS_ALIVE = "ALIVE"
        self.STATUS_DEAD = "DEAD"


const = Constants()


class CommunicationServicer(comm_pb2_grpc.CommunicationServer):
    def __init__(self):
        self.local_averages: List[OrderedDictType] = []
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        self.target_clients = 2
        self.device = "cuda:0"  # Server GPU
        self.state_dict = None

        if not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA device is not available. Ensure CUDA is properly configured."
            )

        try:
            torch.cuda.set_device(self.device)  # Ensure the server runs on cuda:0
            self.model = ModelUtils().get_model("resnet18", "cifar10", self.device, [])
        except RuntimeError as e:
            print(f"Error initializing CUDA device {self.device}: {e}")
            print("Falling back to CPU")
            self.device = "cpu"
            self.model = ModelUtils().get_model("resnet18", "cifar10", self.device, [])
        self.user_ids = {}

    def _generate_ID(self):
        """Generate a random hex ID for a user
        Needs to be thread-safe, although it's unlikely
        collision will occur due to the large range of IDs
        """
        int_id = np.random.randint(
            0, 2**31 - 1
        )  # Generate a random integer between 0 and 2^31 - 1
        random_id = hex(hash(int_id))
        while random_id in self.user_ids:
            int_id = np.random.randint(0, 2**31 - 1)
            random_id = hex(hash(int_id))
        return random_id

    def GetID(self, request, context):
        # whenever a user connects, assign them an random hex ID
        with self.lock:
            random_id = self._generate_ID()
            user_num = len(self.user_ids) + 1
            self.user_ids[random_id] = {
                "user_num": user_num,
                "status": const.STATUS_ALIVE,
                "last_active": time.time(),
            }
            print(f"User {user_num} connected with ID {random_id}")
        return comm_pb2.ID(id=random_id, num=user_num)

    def GetSize(self, request, context):
        # if the last_active time is greater than 5 minutes, mark the user as dead
        with self.lock:
            for user_id, user_info in self.user_ids.items():
                if time.time() - user_info["last_active"] > 300:
                    user_info["status"] = const.STATUS_DEAD
                    print(f'User {user_info["user_num"]} marked as dead')
        # count the number of alive users
        size = len(
            [
                user_id
                for user_id, user_info in self.user_ids.items()
                if user_info["status"] == const.STATUS_ALIVE
            ]
        )
        return comm_pb2.Size(size=size)

    def GetModel(self, request, context):
        # self.state_dict is empty then return self.model.state_dict()
        if not self.state_dict:
            return comm_pb2.Model(buffer=serialize_model(self.model.state_dict()))
        else:
            return comm_pb2.Model(buffer=serialize_model(self.state_dict))

    def SendMessage(self, request, context):
        # update the user's last active time
        user_id = request.id
        self.user_ids[user_id]["last_active"] = time.time()

        print(f"Received message from User {user_id}")

        with self.lock:
            self.local_averages.append(deserialize_model(request.model.buffer))
            self.num_clients = len(self.local_averages)
            print(f"Current number of clients: {self.num_clients}")

            if self.num_clients >= self.target_clients:
                print(f"Notify all clients")
                self.condition.notify_all()

        with self.condition:
            while self.num_clients < self.target_clients:
                print(
                    f"Waiting for clients to reach target ({self.num_clients}/{self.target_clients})"
                )
                self.condition.wait()

        with self.lock:
            self._compute_global_average()
            self.local_averages: List[OrderedDictType] = []
            print("Global average computed")

        # free up memory
        gc.collect()
        torch.cuda.empty_cache()

        print(f"Processed message from User {user_id}")

        return comm_pb2.Empty()

    def SendBye(self, request, context):
        """Remove a user from the list of connected users"""
        with self.lock:
            self.user_ids.pop(request.id)
            print(f"User {request.num} disconnected")
        return comm_pb2.Empty()

    def _compute_global_average(self):
        if not self.local_averages:
            return None

        avg_state_dict = OrderedDict()

        # Sum up the parameters from each local model's state dictionary
        for state_dict in self.local_averages:
            for name, param in state_dict.items():
                if "bn" in name:
                    continue  # Skip batch norm layers
                if name not in avg_state_dict:
                    avg_state_dict[name] = param.clone().to(self.device)
                else:
                    avg_state_dict[name] += param.to(self.device)

        # Divide the summed parameters by the number of local models to get the average
        for name, param in avg_state_dict.items():
            avg_state_dict[name] = param / float(len(self.local_averages))

        self.state_dict = avg_state_dict


def serve():
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ("grpc.max_send_message_length", 50 * 1024 * 1024),  # 50MB
            ("grpc.max_receive_message_length", 50 * 1024 * 1024),  # 50MB
        ],
    )
    comm_pb2_grpc.add_CommunicationServerServicer_to_server(
        CommunicationServicer(), server
    )
    server.add_insecure_port("[::]:50051")
    server.start()
    print("Server started")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
