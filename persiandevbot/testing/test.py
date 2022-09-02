import multiprocessing
import time

from utils.keep_alive import KeepAlive

def keppalive():
    kp = KeepAlive("localhost", 2380)
    kp.run()

def test(x):
    time.sleep(10)
    print(f"{x=}")

if __name__ == "__main__":
    k = multiprocessing.Process(target=lambda: KeepAlive("localhost", 2380).run())
    t = multiprocessing.Process(target=test, args=(100,))
    k.start()
    t.start()
    print("After")
    k.join()
