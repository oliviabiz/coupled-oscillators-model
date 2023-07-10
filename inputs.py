import numpy as np
import random

""" Functions to create different types of inputs """

def pattern(duration, intervals):
    """Creates inputs of given duration according to pattern defined by intervals """
    # intervals: list of inter-stimulus intervals < 360ms in ordered sequence

    x = np.linspace(0, duration, duration, endpoint=False)
    stim = np.zeros(np.shape(x))
    stim_pattern = np.empty(np.shape(x))

    # determine initial stimulus occurence
    stim_time = random.randint(0, intervals[0])

    i = 0 # index of current ISI in intervals to use

    # add next stimuli after ISI determined by intervals
    while stim_time < duration:
        stim[stim_time] = 1
        stim_pattern[stim_time] = i
        stim_time += intervals[i]
        i = (i + 1) % len(intervals)
    return x, stim, stim_pattern


def drop_stim(self, duration, interval, drop_rate=0.5):
    """ Creates inputs at constant interval where some inputs are randomly missing """
    x, stim, _ = pattern(duration, [interval])

    stim_present = np.where(stim == 1)[0]
    drop_num = round(drop_rate * len(stim_present))
    drop = np.random.choice(stim_present, drop_num)
    stim_present = np.setdiff1d(stim_present, drop)
    new_stim = np.zeros(stim.shape)
    new_stim[stim_present] = 1
    self.stim = new_stim

def multisensory_stimuli(duration, modalities):
    stimuli = np.zeros((modalities, duration))

    interval = 720
    stim_time = 300

    soas = []
    trials = []  # trial begin
    trial_end = []
    leads = []

    
    audio_index = 0
    # asynchronies = np.arange(-150, 175, 25)
    # asynchronies = np.arange(-75, 75, 5)
    asynchronies = np.arange(-100,125, 5)

    while stim_time < duration:
        ### Procedure:
        #  Generate random SOA (positive or negative)
        # If negative, place audio first
        # If positive, place visual first
        # If 0, place at same time

        SOA = random.choice(asynchronies)

        if SOA < 0:
            lead = "audio"
        elif SOA > 0:
            lead = "visual"
        elif SOA == 0:
            lead = None

        soas.append(SOA)
        leads.append(lead)
        trials.append(min(stim_time, stim_time + SOA))
        trial_end.append(max(stim_time, stim_time + SOA))

        for i in range(modalities):
            stim = stimuli[i]
            if i == audio_index:
                try:
                    stim[stim_time + SOA] = 1
                except:
                    print("Desired stimulus onset outside of session duration")
            else:
                stim[stim_time] = 1

        jitter = random.randint(-250, 250)
        jitter = 0
        stim_time += interval + jitter
        

    trials = np.array(trials)
    trial_end = np.array(trial_end)
    return stimuli, trials, trial_end, leads, soas