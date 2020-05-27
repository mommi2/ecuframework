import threading


def looped(f, seconds=None, daemon=True, *args, **kwargs):
    stopped = threading.Event()

    if seconds is None:
        def loop():
            while not stopped.isSet():
                f(*args, **kwargs)
    else:
        def loop():
            while not stopped.wait(seconds):  # until stopped
                f(*args, **kwargs)

    t = threading.Thread(target=loop, daemon=daemon)
    t.start()
    return stopped