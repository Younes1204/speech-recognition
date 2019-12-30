from sys import byteorder
from array import array
from struct import pack

import pyaudio
import wave

from js2py.base import xrange

import speech_recognition as sr

THRESHOLD = 500
CHUNK_SIZE = 2048
FORMAT = pyaudio.paInt16
RATE = 44100


def is_silent(snd_data):
    return max(snd_data) < THRESHOLD


def normalize(snd_data):
    MAXIMUM = 16384
    times = float(MAXIMUM) / max(abs(i) for i in snd_data)

    r = array('h')
    for i in snd_data:
        r.append(int(i * times))
    return r


def trim(snd_data):
    def _trim(snd_data):
        snd_started = False
        r = array('h')

        for i in snd_data:
            if not snd_started and abs(i) > THRESHOLD:
                snd_started = True
                r.append(i)

            elif snd_started:
                r.append(i)
        return r

    snd_data = _trim(snd_data)
    snd_data.reverse()
    snd_data = _trim(snd_data)
    snd_data.reverse()
    return snd_data


def add_silence(snd_data, seconds):
    r = array('h', [0 for i in xrange(int(seconds * RATE))])
    r.extend(snd_data)
    r.extend([0 for i in xrange(int(seconds * RATE))])
    return r


def record():
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=1, rate=RATE, input=True, output=True, frames_per_buffer=CHUNK_SIZE)

    num_silent = 0
    snd_started = False

    r = array('h')

    while 1:
        snd_data = array('h', stream.read(CHUNK_SIZE))
        if byteorder == 'big':
            snd_data.byteswap()
        r.extend(snd_data)

        silent = is_silent(snd_data)

        if silent and snd_started:
            num_silent += 1
        elif not silent and not snd_started:
            snd_started = True

        if snd_started and num_silent > 30:
            break

    sample_width = p.get_sample_size(FORMAT)
    stream.stop_stream()
    stream.close()
    p.terminate()

    r = normalize(r)
    r = trim(r)
    r = add_silence(r, 0.5)
    return sample_width, r


def record_to_file(path):
    sample_width, data = record()
    data = pack('<' + ('h' * len(data)), *data)

    wt = wave.open(path, 'wb')
    wt.setnchannels(1)
    wt.setsampwidth(sample_width)
    wt.setframerate(RATE)
    wt.writeframes(data)
    wt.close()

    r = sr.Recognizer()
    with sr.AudioFile(path) as source:
        audio_data = r.record(source)
        text = r.recognize_google(audio_data)
        print("Voici ce que vous avez enregistré : " + text)


if __name__ == '__main__':
    print("please speak a word into the microphone")
    record_to_file('demo.wav')
    print("done - result written to demo.wav")

