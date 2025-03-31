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