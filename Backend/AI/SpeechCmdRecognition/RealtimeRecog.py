import sounddevice as sd
import numpy as np
import tensorflow as tf

CHANNELS = 1
RATE = 16000
GSCmdV2Categs = {
            'unknown': 0,
            'silence': 0,
            '_unknown_': 0,
            '_silence_': 0,
            '_background_noise_': 0,
            'yes': 2,
            'no': 3,
            'up': 4,
            'down': 5,
            'left': 6,
            'right': 7,
            'on': 8,
            'off': 9,
            'stop': 10,
            'go': 11,
            'zero': 12,
            'one': 13,
            'two': 14,
            'three': 15,
            'four': 16,
            'five': 17,
            'six': 18,
            'seven': 19,
            'eight': 20,
            'nine': 1,
            'backward': 21,
            'bed': 22,
            'bird': 23,
            'cat': 24,
            'dog': 25,
            'follow': 26,
            'forward': 27,
            'happy': 28,
            'house': 29,
            'learn': 30,
            'marvin': 31,
            'sheila': 32,
            'tree': 33,
            'visual': 34,
            'wow': 35}
command_list= {v: k for k, v in GSCmdV2Categs.items() if v != 0}
from SpeechModels import AttRNNSpeechModel

model = AttRNNSpeechModel(36, samplingrate=RATE, inputLength=RATE)
model.load_weights('model-attRNN.h5')
model.summary()


def record_audio():
    seconds = 1 
    audio = sd.rec(int(seconds * RATE), samplerate=RATE, channels=CHANNELS, dtype=np.int16)
    sd.wait()
    return np.squeeze(audio)


def predict_mic():
    command = None
    audio = record_audio()
    audio = audio / 32768
    sig = tf.convert_to_tensor(audio)
    sig = np.expand_dims(sig, axis=0)

    prediction = model.predict(sig, verbose=0)
    probs = tf.nn.softmax(prediction, axis=1)
    prob, index = tf.reduce_max(probs, axis=1), tf.argmax(probs, axis=1)
    if prob.numpy()[0] > 0.07:
        print(prob.numpy()[0],command_list[index.numpy()[0]])
    return command


if __name__ == "__main__":
    while True:
        command = predict_mic()
        if command == "stop":
            break
