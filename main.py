# This Python file uses the following encoding: utf-8
import time
import random
import math
from queue import PriorityQueue
import re

NUM_OF_DEVICES = 7
NUM_OF_PRODUCERS = 5
BUFFER_SIZE = 3
TOTAL_REQUESTS = 100
lambda_ = 0.975
kaos = {"event": [], "num": [], "time": [], "flag": []}
alpha = 1.1
beta = 1.0
request_per_source = [[] for _ in range(NUM_OF_PRODUCERS)]
out_file = open('smo_log.txt', 'w')

def get_device_processing_time(alpha, beta):
    return random.uniform(alpha, beta) * 10


def get_seconds_and_milliseconds():
    return time.time() // 0.001 % 10000000 / 1000


def generate_request_time():
    return (-1 / lambda_) * math.log(random.random()) * 10


def log_to_file(step, buffer, kaos):
    pass
    out_file.write(f"Шаг {step}:\n")
    out_file.write("Состояние буфера:\n")
    out_file.write("Позиция\t\t Время\t\t Источник\t\t Заявка\n")
    for i in range(len(buffer)):
        if buffer[i] is None:
            out_file.write(f"Позиция {i}\t 0.0\t\t 0\t\t\t 0\n")
        else:
            out_file.write(f"Позиция {i}\t {buffer[i][1]:.3f}\t\t {buffer[i][2]}\t\t\t {buffer[i][0]}\n")
    out_file.write("\nКалендарь особых событий:\n")
    for i in range(len(kaos['event'])):
        out_file.write(f"  Тип: {kaos['event'][i]} {kaos["num"][i]}, Tос: {kaos['time'][i]:.3f}, ПР: {kaos['flag'][i]}\n")
    out_file.write("\n")

class SMO:
    def __init__(self):
        self.devices = PriorityQueue(maxsize=NUM_OF_DEVICES)
        self.buffer = [None] * BUFFER_SIZE
        self.buffer_pointer = 0
        self.logs = []
        self.processed_requests = 0
        self.rejected_requests = 0
        self.step = 0
        self.start_time = get_seconds_and_milliseconds()
        self.last_dev_proc_time = 0
        self.total_requests = TOTAL_REQUESTS
        self.bufferSize = BUFFER_SIZE
        self.modeling_end = True
        self.num_of_sources = NUM_OF_PRODUCERS
        self.num_of_devices = NUM_OF_DEVICES
        self.device_work_time = [[] for _ in range(NUM_OF_DEVICES)]
        self.time_of_each_req_serving = [[] for _ in range(NUM_OF_PRODUCERS)]


    def add_request_to_buffer(self, request, time_arrival):
        num1, num2 = self.extract_numbers(request)
        start_pointer = self.buffer_pointer
        while self.buffer[self.buffer_pointer] is not None:
            self.buffer_pointer = (self.buffer_pointer + 1) % self.bufferSize
            if self.buffer_pointer == start_pointer:
                print(f"Буфер заполнен. Заявке {self.buffer[self.buffer_pointer][0]} отказано.")
                self.buffer[self.buffer_pointer] = (f"Заявка {num1}-{num2}", time_arrival, num1)
                self.rejected_requests += 1
                self.buffer_pointer = (self.buffer_pointer + 1) % self.bufferSize
                return
        self.buffer[self.buffer_pointer] = (f"Заявка {num1}-{num2}", time_arrival, num1)
        self.buffer_pointer = (self.buffer_pointer + 1) % self.bufferSize
        print(f"Заявка {num1}-{num2} добавлена в буфер на позицию {self.buffer_pointer}")


    def check_buffer(self):
        flag = False
        for i in range(BUFFER_SIZE):
            if self.buffer[i] is not None and not self.devices.full():
                self.devices.put(self.buffer[i][0])
                print(f"{self.buffer[i][0]} перемещена из буфера в прибор.")
                flag = True
                self.buffer[i] = None
                break

        return flag

    def process_request(self):
        while (self.modeling_end):
            a = self.next_event()
            if a >= self.num_of_sources and a < (self.num_of_sources + self.num_of_devices):
                if (self.check_buffer() == True):
                    request = self.devices.get()
                    num1, num2 = self.extract_numbers(request)
                    process_time = get_device_processing_time(alpha, beta)
                    self.device_work_time[a-self.num_of_sources].append(process_time)
                    kaos["time"][a] = kaos["time"][a] + process_time
                    self.time_of_each_req_serving[num1-1].append(process_time)
                    self.log_state()
                    self.last_dev_proc_time = kaos["time"][a]
                else:
                    request = self.devices.get()
                    kaos["time"][a] = 0
                    kaos["flag"][a] = 1
                    self.log_state()

            elif (a >= 0 and a < self.num_of_sources):
                req = request_per_source[a][-1]
                num1, num2 = self.extract_numbers(req)
                request = f"Заявка {num1}-{num2 + 1}"
                print(f"Источник {a+1} сгенерировал Заявку {num1}-{num2 + 1}")
                request_per_source[a].append(request)
                for i in range(self.num_of_sources, self.num_of_devices + self.num_of_sources):
                    if kaos["flag"][i] == 1:
                        self.devices.put(request)
                        process_time = get_device_processing_time(alpha, beta)
                        kaos["time"][i] = kaos["time"][a] + process_time
                        self.time_of_each_req_serving[num1 - 1].append(process_time)
                        self.device_work_time[i-self.num_of_sources].append(process_time)
                        kaos["flag"][i] = 0
                        self.last_dev_proc_time = kaos["time"][i]
                        self.total_requests -= 1
                        if (self.total_requests <= 0):
                            kaos["time"][a] = 0
                            kaos["flag"][a] = 1
                            self.log_state()
                        else:
                            request_time = generate_request_time()
                            kaos["time"][a] = kaos["time"][a] + request_time
                            self.log_state()
                        print(f"{request} была добавлена на Прибор {i+1 - self.num_of_sources}")
                        break
                    if kaos["flag"][i] == 0:
                        continue
                else:
                    self.add_request_to_buffer(request, kaos["time"][a])
                    request_time = generate_request_time()
                    kaos["time"][a] = kaos["time"][a] + request_time
                    self.log_state()
                    self.total_requests -= 1
            else:

                self.modeling_end = False

    def extract_numbers(self, request):
        match = re.search(r"(\d+)-(\d+)", request)
        if match:
            return int(match.group(1)), int(match.group(2))
        return None, None

    def next_event(self):
        min_time = 9999999999
        for i in range(len(kaos["event"])):
            if kaos["flag"][i] != 1:
                if kaos["time"][i] < min_time:
                    min_time = kaos["time"][i]
        if min_time != 9999999999:
            min_index = kaos["time"].index(min_time)
            return min_index
        else:
            return -1
    def start_initialization_kaos(self):
        for i in range(self.num_of_sources):
            kaos["event"].append("Источник")
            kaos["num"].append(i+1)
            kaos["time"].append(0)
            kaos["flag"].append(1)
        for i in range(self.num_of_devices):
            kaos["event"].append("Прибор")
            kaos["num"].append(i+1)
            kaos["time"].append(0)
            kaos["flag"].append(1)

    def gen_first_requests(self):
        for i in range(self.num_of_sources):
            request = f"Заявка от источника {i+1}-1"
            kaos["time"][i] = self.start_time + generate_request_time()
            kaos["flag"][i] = 0
            request_per_source[i].append(request)
        self.log_state()
        self.total_requests -= self.num_of_sources

    def log_state(self):
        self.step += 1
        log_to_file(self.step, self.buffer, kaos)

if __name__ == "__main__":
    smo = SMO()
    smo.start_initialization_kaos()
    smo.gen_first_requests()
    smo.process_request()