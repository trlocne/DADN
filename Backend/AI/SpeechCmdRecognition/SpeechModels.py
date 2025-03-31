import tensorflow as tf
from tensorflow.keras.models import Model, load_model

from tensorflow.keras import layers as L
from tensorflow.keras import backend as K
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, LearningRateScheduler
from tensorflow.keras import backend as K
from tensorflow.keras import optimizers
import os
import itertools
import numpy as np
from tqdm import tqdm
import tensorflow as tf
import matplotlib.pyplot as plt


def WAV2Numpy(folder, sr=None):
    """
    Recursively converts WAV to numpy arrays.
    Deletes the WAV files in the process

    folder - folder to convert.
    """
    allFiles = []
    for root, dirs, files in os.walk(folder):
        allFiles += [os.path.join(root, f) for f in files
                     if f.endswith('.wav')]

    for file in tqdm(allFiles):
        x = tf.io.read_file(str(file))
        y, sample_rate = tf.audio.decode_wav(x, desired_channels=1, desired_samples=16000,)

        # if we want to write the file later
        np.save(file + '.npy', y.numpy())
        os.remove(file)

# this was supposed to be tfio.audio.spectrogram
def spectrogram_fn(input_signal, nfft, window, stride, name=None):
    """
    Create spectrogram from audio.
    Args:
      input: An 1-D audio signal Tensor.
      nfft: Size of FFT.
      window: Size of window.
      stride: Size of hops between windows.
      name: A name for the operation (optional).
    Returns:
      A tensor of spectrogram.
    """

    # TODO: Support audio with channel > 1.
    return tf.math.abs(
        tf.signal.stft(
            input_signal,
            frame_length=window,
            frame_step=stride,
            fft_length=nfft,
            window_fn=tf.signal.hann_window,
            pad_end=True,
        )
    )

def normalized_mel_spectrogram(x, sr=16000, n_mel_bins=80):
    spec_stride = 128
    spec_len = 1024

    spectrogram = spectrogram_fn(
        x, nfft=spec_len, window=spec_len, stride=spec_stride
    )

    num_spectrogram_bins = spec_len // 2 + 1  # spectrogram.shape[-1]
    lower_edge_hertz, upper_edge_hertz = 40.0, 8000.0
    num_mel_bins = n_mel_bins
    linear_to_mel_weight_matrix = tf.signal.linear_to_mel_weight_matrix(
      num_mel_bins, num_spectrogram_bins, sr, lower_edge_hertz,
      upper_edge_hertz)
    mel_spectrograms = tf.tensordot(spectrogram, linear_to_mel_weight_matrix, 1)
    mel_spectrograms.set_shape(spectrogram.shape[:-1].concatenate(linear_to_mel_weight_matrix.shape[-1:]))

    log_mel_spectrograms = tf.math.log(mel_spectrograms + 1e-6)
    avg = tf.math.reduce_mean(log_mel_spectrograms)
    std = tf.math.reduce_std(log_mel_spectrograms)

    return (log_mel_spectrograms - avg) / std

def get_melspec_model(iLen=None):
    inp = L.Input((iLen,), name='input')
    mel_spec = normalized_mel_spectrogram(inp)
    melspecModel = Model(inputs=inp, outputs=mel_spec, name='normalized_spectrogram_model')
    return melspecModel


def AttRNNSpeechModel(nCategories, samplingrate=16000,
                      inputLength=16000, rnn_func=L.LSTM):
    # simple LSTM
    sr = samplingrate
    iLen = inputLength

    inputs = L.Input((inputLength,), name='input')

    m =  get_melspec_model(iLen=inputLength)
    m.trainable = False

    x = m(inputs)
    x = tf.expand_dims(x, axis=-1, name='mel_stft')

    x = L.Conv2D(10, (5, 1), activation='relu', padding='same')(x)
    x = L.BatchNormalization()(x)
    x = L.Conv2D(1, (5, 1), activation='relu', padding='same')(x)
    x = L.BatchNormalization()(x)

    # x = Reshape((125, 80)) (x)
    # keras.backend.squeeze(x, axis)
    x = L.Lambda(lambda q: K.squeeze(q, -1), name='squeeze_last_dim')(x)

    x = L.Bidirectional(rnn_func(64, return_sequences=True)
                        )(x)  # [b_s, seq_len, vec_dim]
    x = L.Bidirectional(rnn_func(64, return_sequences=True)
                        )(x)  # [b_s, seq_len, vec_dim]

    xFirst = L.Lambda(lambda q: q[:, -1])(x)  # [b_s, vec_dim]
    query = L.Dense(128)(xFirst)

    # dot product attention
    attScores = L.Dot(axes=[1, 2])([query, x])
    attScores = L.Softmax(name='attSoftmax')(attScores)  # [b_s, seq_len]

    # rescale sequence
    attVector = L.Dot(axes=[1, 1])([attScores, x])  # [b_s, vec_dim]

    x = L.Dense(64, activation='relu')(attVector)
    x = L.Dense(32)(x)

    output = L.Dense(nCategories, activation='softmax', name='output')(x)

    model = Model(inputs=[inputs], outputs=[output])

    return model
