class LogEvent:
    def __init__(self, line):
        parts = line.strip("\n").split(" ", 6)
        (self.timestamp, self.node, self.process, self.thread, self.type, self.location, self.text) = parts

    def thread_id(self):
        return "%s %s %s" % (self.node, self.process, self.thread)

    def event_str(self):
        return "%s %s:%s" % (self.location, self.type, self.text)

    def __str__(self):
        return self.thread_id() + " " + self.event_str()


class Event:
    def __init__(self, row):
        (
            self.id,
            self.thread_id,
            self.start_location, self.end_location,
            self.start_time, self.end_time,
            self.start_type, self.end_type,
            self.start_text, self.end_text,
        ) = row
        # self.node, self.process, self.thread,
