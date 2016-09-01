import numpy as np
import vdmlab as vdm
from .objects import Position


def bayesian_prob(counts, tuning_curves, binsize, min_neurons=1, min_spikes=1):
    """Computes the bayesian probability of location based on spike counts.

    Parameters
    ----------
    counts : np.array
        Where each inner array is the number of spikes (int) in each bin for an individual neuron.
    tuning_curves : np.array
        Where each inner array is the tuning curve (floats) for an individual neuron.
    binsize : float
        Size of the time bins.
    min_neurons : int
        Mininum number of neurons active in a given bin. Default is 1.
    min_spikes : int
        Mininum number of spikes in a given bin. Default is 1.

    Returns
    -------
    prob : np.array
        Where each inner array is the probability (floats) for an individual neuron by location bins.

    Notes
    -----
    If a bin does not meet the min_neuron/min_spikes requirement, that bin's probability
    is set to nan. To convert it to 0s instead, use : prob[np.isnan(prob)] = 0 on the output.

    """
    n_time_bins = np.shape(counts)[1]
    n_position_bins = np.shape(tuning_curves)[1]

    likelihood = np.empty((n_time_bins, n_position_bins)) * np.nan

    # Ignore warnings when inf created in this loop
    error_settings = np.seterr(over='ignore')
    for idx in range(n_position_bins):
        valid_idx = tuning_curves[:, idx] > 1  # log of 1 or less is negative or invalid
        if np.any(valid_idx):
            # event_rate is the lambda in this poisson distribution
            event_rate = tuning_curves[valid_idx, idx][..., np.newaxis] ** counts[valid_idx]
            prior = np.exp(-binsize * np.sum(tuning_curves[valid_idx, idx]))

            # Below is the same as
            # likelihood[:, idx] = np.prod(event_rate, axis=0) * prior * (1/n_position_bins)
            # only less likely to have floating point issues, though slower
            likelihood[:, idx] = np.exp(np.sum(np.log(event_rate), axis=0)) * prior * (1/n_position_bins)
    np.seterr(**error_settings)

    # Set any inf value to be largest float
    largest_float = np.finfo(float).max
    likelihood[np.isinf(likelihood)] = largest_float
    likelihood /= np.nansum(likelihood, axis=1)[..., np.newaxis]

    # Remove bins with too few neurons that that are active
    # a neuron is considered active by having at least min_spikes in a bin
    n_active_neurons = np.sum(counts >= min_spikes, axis=0)
    likelihood[n_active_neurons < min_neurons] = np.nan

    return likelihood


def decode_location(likelihood, pos_centers, time_centers):
    """Finds the decoded location based on the centers of the position bins.

    Parameters
    ----------
    likelihood : np.array
        With shape(n_timebins, n_positionbins)
    pos_centers : np.array
    time_centers : np.array

    Returns
    -------
    decoded : np.array
        Estimate of decoded position.

    """
    prob_rows = np.sum(np.isnan(likelihood), axis=1) < likelihood.shape[1]
    max_decoded_idx = np.nanargmax(likelihood[prob_rows], axis=1)

    prob_decoded = pos_centers[max_decoded_idx]

    decoded_pos = np.empty((likelihood.shape[0], pos_centers.shape[1])) * np.nan
    decoded_pos[prob_rows] = prob_decoded

    decoded_pos = np.squeeze(decoded_pos)

    decoded = vdm.Position(decoded_pos, time_centers)

    return decoded


def remove_teleports(position, speed_thresh, min_length):
    """Removes positions above a certain speed threshold

    Parameters
    ----------
    position : vdmlab.Position
    speed_thresh : int
        Maximum speed to consider natural rat movements. Anything
        above this theshold will not be included in the filtered positions.
    min_length : int
        Minimum length for a sequence to be included in filtered positions.

    Returns
    -------
    filtered_position : vdmlab.Position

    """
    velocity = np.squeeze(position.speed().data)

    split_idx = np.where(velocity >= speed_thresh)[0]
    keep_idx = [idx for idx in np.split(np.arange(position.n_samples), split_idx) if idx.size >= min_length]
    if len(keep_idx) == 0:
        raise ValueError("resulted in all position samples removed. Adjust min_length or speed_thresh.")

    return position[np.hstack(keep_idx)]
