"""Incidentes de presencia: intervalos observados, sin extrapolar la última muestra."""

from bisect import bisect_left
from collections import defaultdict
from datetime import datetime


class OutageTimeline:
    def __init__(self, rows):
        intervals = defaultdict(list)
        previous = None
        start = last = None
        for row in rows:
            key = (row["device_id"], row["session_id"])
            stamp = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")).timestamp()
            if key != previous:
                if start is not None:
                    intervals[previous[0]].append((start, last))
                start = None
            if row["presence"]:
                if start is not None:
                    intervals[key[0]].append((start, stamp))
                    start = None
            elif start is None:
                start = stamp
            previous, last = key, stamp
        if start is not None:
            intervals[previous[0]].append((start, last))
        self.intervals = {}
        self.ends = {}
        for device, values in intervals.items():
            merged = []
            for begin, end in sorted(values):
                if merged and begin <= merged[-1][1]:
                    merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
                else:
                    merged.append((begin, end))
            self.intervals[device] = merged
            self.ends[device] = [end for _, end in merged]

    def count(self, device):
        return len(self.intervals.get(device, ()))

    def bucket(self, device, start, resolution):
        end = start + resolution
        count, duration = 0, 0.0
        intervals = self.intervals.get(device, ())
        index = bisect_left(self.ends.get(device, ()), start)
        while index < len(intervals):
            begin, finish = intervals[index]
            if begin >= end:
                break
            count += int(start <= begin < end)
            duration += max(0, min(finish, end) - max(begin, start))
            index += 1
        return count, duration


def load_outages(database, session_id=None):
    query = """
        SELECT device_id,session_id,timestamp,MAX(presence) presence FROM samples
        WHERE check_type IN ('availability','ping','arp')
    """
    values = ()
    if session_id is not None:
        query += " AND session_id=?"
        values = (session_id,)
    query += " GROUP BY device_id,session_id,timestamp ORDER BY device_id,session_id,julianday(timestamp),timestamp"
    return OutageTimeline(database.execute(query, values))
