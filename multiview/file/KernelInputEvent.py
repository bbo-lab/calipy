from construct import *
import numpy as np

# 32bit because we assume ARM7 data
TimeVal = Struct(
    "sec"  / Int32ul,
    "usec"  / Int32ul
)

# See include/linux/input.h
InputEvent = Struct(
    "time" / TimeVal,
    "type" / Int16ul,
    "code" / Int16ul,
    "value" / Int32sl,
)

# Data from /dev/input/eventX
InputEventStream = GreedyRange(
    InputEvent
)

# Type field enum values
INPUT_TYPE_MISC = 4

# Code field enum values
INPUT_EVENT_X = 0
INPUT_EVENT_Y = 1
INPUT_EVENT_Z = 2

INPUT_EVENT_TIME_MSB = 4
INPUT_EVENT_TIME_LSB = 7

def loadKernelInputEvents(filename):
    """Loads kernel input events from file"""
    with open(filename, "rb") as f:
        return InputEventStream.parse_stream(f)

    
def loadLSM6DSData(filename, calib=[0, 0, 0]):
    events = loadKernelInputEvents(filename)
    
    # Only keep input event of correct type
    events = [e for e in events if e.type == INPUT_TYPE_MISC]

    # Get ride of incomplete datapoints
    while events[0].code != INPUT_EVENT_X:
        events.pop(0)
    while events[-1].code != INPUT_EVENT_TIME_LSB:
        events.pop()
    
    # Allocate return values
    max_size = int(len(events) / 5)
    data = np.zeros([max_size, 3], dtype=np.int16)
    ts   = np.zeros(max_size, dtype=np.uint64)
    
    # Go through remaining events and combine events into datapoints
    i = 0 # next event to check
    j = 0 # next datapoint to extract
    while i < len(events) - 4:
        # Events of one datapoint are sent right after each other
        if events[i + 0].code == INPUT_EVENT_X and \
           events[i + 1].code == INPUT_EVENT_Y and \
           events[i + 2].code == INPUT_EVENT_Z and \
           events[i + 3].code == INPUT_EVENT_TIME_MSB and \
           events[i + 4].code == INPUT_EVENT_TIME_LSB:
            
            group = events[i:i+5]
            
            # Make sure that timestamps do not differ or only by exactly 400 (fixme: once)
            diff = np.diff([1000000 * e.time.sec + e.time.usec for e in group])
            if any(diff) and sum(abs(diff)) != 400:
                print("Warning: Package timimg error: " + str(diff))
           
            # Retrieve and correct data
            data[j, 0] = group[0].value - calib[0]
            data[j, 1] = group[1].value - calib[1]
            data[j, 2] = group[2].value - calib[2]

            ts[j] = (group[3].value << 32) | group[4].value & 0xffffffff
            
            # Skip to next event and datapoint
            i += 5
            j += 1
        else:
            # Save beginning for logging purpose
            start = i
            
            # Current event is not the start of a complete package
            i += 1
            
            # Find potential new beginning
            while events[i].code != INPUT_EVENT_X and i < len(events):
                i += 1
            
            # Inform about lost datapoint fragments
            print('Warning: broken package at {} ({}): '.format(j, start) + \
                  '-'.join([str(e.code) for e in events[start:i]]))
    
    # Remove extra data reserved for skipped events
    return ts[:j], data[:j, :]

def convertLSM6DSGyro(data, gyroRange=2000):
    """
    Converts raw data values to angle change in dps
    """
    divisor = gyroRange / 125
    if gyroRange == 245:
        divisor = 2

    return data * 4.375 * divisor / 1000

def convertLSM6DSAccel(data, accelRange=16):
    """
    Convert raw data values to acceleration in g
    """
    return data * 0.061 * (accelRange >> 1) / 1000
