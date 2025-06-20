import obspython as obs
import time

class Recorder:
    def __init__(self):
        self.start_time = time.time()
        self.interval = 20  # 20 seconds interval
        self.script_load(None)

    def script_description(self):
        return "Auto save recordings every 20 seconds"

    def script_load(self, settings):
        self.timer_start()

    def timer_start(self):
        self.timer = obs.timer_add(self.check_time, 1000)  # Check every second

    def check_time(self):
        if time.time() - self.start_time >= self.interval:
            obs.obs_frontend_recording_stop()
            time.sleep(2)
            obs.obs_frontend_recording_start()
            self.start_time = time.time()

    def script_unload(self):
        obs.timer_remove(self.check_time)

recorder = Recorder()
