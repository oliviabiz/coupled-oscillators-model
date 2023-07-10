from experiments import *
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import norm


""" Functions for analyzing results of multisensory / synchrony experiment data  """


# Define experiment constants
V_repeat = 1
A_repeat = 2
V_nonrepeat = 3
A_nonrepeat = 4


rep_dict = {
    V_repeat: "V_repeat",
    A_repeat: "A_repeat",
    V_nonrepeat: "V_nonrepeat",
    A_nonrepeat: "A_nonrepeat",
}


# Returns dictionary of multisensory experiment results summarized by value, not by trial
def summarize(results):
    num_trials = len(results)
    keys = list(results[0].keys())
    num_keys = len(keys)
    all_results = {}
    for i in range(num_keys):
        key = keys[i]
        values = [results[i][key] for i in range(num_trials)]
        all_results[key] = values
    return all_results

# Returns current trial response associated with previous trial info
def shift_results(results):
    prev_results = {}
    num_trials = len(results["lead"]) - 1
    prev_results["response"] = np.array(results["response"][1:])
    prev_results["lead"] = np.array(results["lead"][1:])
    # prev_results["lead"][0] = "Null"
    prev_results["prev_lead"] = np.array(results["lead"][:-1])
    prev_results["soa"] = np.array(results["soa"][1:])
    prev_results["repeat"] = np.zeros((num_trials, 1))

    for i in range(num_trials):  # range(len(prev_results["prev_lead"])):
        prev_lead = prev_results["prev_lead"][i]
        curr_lead = prev_results["lead"][i]
        repeat = None

        if prev_lead == "visual":
            repeat = V_repeat if curr_lead == "visual" else V_nonrepeat
        elif prev_lead == "audio":
            repeat = A_repeat if curr_lead == "audio" else A_nonrepeat

        prev_results["repeat"][i] = repeat

    return prev_results


# Given a list of responses (+/- 1), returns percent of trials marked as synchronous
def sync_percent(responses):
    sync = len(np.where(responses == 1)[0])
    # total = len(responses)
    total = sync + len(np.where(responses == -1)[0])
    return 0 if total == 0 else sync / total


# Given a list of responses (+/- 1), returns ratio of async:sync responses
def sync_ratio(responses):
    sync = len(np.where(responses == 1)[0])
    a_sync = len(np.where(responses == -1)[0])
    return 0 if sync == 0 else a_sync / sync


def get_soa_synchrony(soa, trials):
    idx = np.where(trials["soa"] == soa)[0]
    trials = trials["response"][idx]
    pc = sync_percent(trials)
    return pc


# Define the Gaussian function
def gauss(x, amp, mu, sigma):
    y = amp * np.exp(-((x - mu) ** 2) / (2 * sigma ** 2))
    return y


def gauss_params(x, y):
    # initial_params
    n = len(x)
    amp = max(y)
    mean = sum(x * y) / n
    sigma = sum(y * (x - mean) ** 2) / n
    init_params = [amp, mean, sigma]
    # fitting
    popt, pcov = curve_fit(f=gauss, xdata=x, ydata=y, p0=init_params)
    return popt


def fit_gauss(xdata, ydata):
    xdata = np.asarray(xdata)
    ydata = np.asarray(ydata)

    fit_params = gauss_params(xdata, ydata)
    x_test = np.linspace(min(xdata), max(xdata), 1000)
    y_test = gauss(x_test, *fit_params)
    return x_test, y_test


def get_mode(x, y):
    peak_value = max(y)
    peak_loc = np.where(y == peak_value)[0][0]
    mode = x[peak_loc]
    return mode, peak_value

# Analyze results of multisensory experiment: returns amount of temporal recalibration
def analyze(results, plot=False):
    summ = summarize(results)
    prev = shift_results(summ)

    unique_soa = list(set(prev["soa"]))
    unique_soa.sort()
    percent_sync_a = []
    percent_sync_v = []
    percent_sync = []

    # Filter based on previous trial asynchrony condition
    prev_a_idx = np.where(prev["prev_lead"] == "audio")
    prev_a = {k: v[prev_a_idx] for k, v in prev.items()}
    prev_v_idx = np.where(prev["prev_lead"] == "visual")
    prev_v = {k: v[prev_v_idx] for k, v in prev.items()}

    # Histogram - how many of each unique SOAs
    soa_freq = []

    # Calculate percentage synchronous responses for each possible SOA
    for soa in unique_soa:
        soa_freq.append(len(np.where(prev["soa"] == soa)[0]))
        percent_sync.append(get_soa_synchrony(soa, prev))
        percent_sync_a.append(get_soa_synchrony(soa, prev_a))
        percent_sync_v.append(get_soa_synchrony(soa, prev_v))

    # Fit Gaussians to response data
    x_a, y_a = fit_gauss(unique_soa, percent_sync_a)
    x_v, y_v = fit_gauss(unique_soa, percent_sync_v)

    a_mode, a_mode_y = get_mode(x_a, y_a)
    v_mode, v_mode_y = get_mode(x_v, y_v)
    tr = v_mode - a_mode

    # Visualize
    if plot:
        plt.figure()
        plt.plot(
            unique_soa, np.multiply(percent_sync_a, 100), ".", label="t-1:A", color="blue"
        )
        plt.plot(x_a, np.multiply(y_a, 100), "-", color="blue")

        plt.plot(
            unique_soa, np.multiply(percent_sync_v, 100), ".", label="t-1:V", color="red"
        )
        plt.plot(x_v, np.multiply(y_v, 100), "-", color="red")

        plt.ylabel("percent synchronous responses (%)")
        plt.xlabel("SOA (ms)")
        # plt.legend(
        #     [
        #         "t-1:A (data)",
        #         "t-1:A (fit)",
        #         "t-1:V (data)",
        #         "t-1:V (fit)",
        #     ]
        # )
        plt.legend()

        plt.vlines(a_mode, ymin=0, ymax=100 * a_mode_y, color="blue", linestyles="dashed")
        plt.vlines(v_mode, ymin=0, ymax=100 * v_mode_y, color="red", linestyles="dashed")
        plt.ylim([-5, 105])
        plt.title(f"temporal recalibration = {round(tr,2)} ms")

        plt.show(block=False)
        print("temporal recalibration =", round(tr, 5))

    return tr

# Run a multisensory experiment and extract behavioural data (temporal recalibration)
def run_experiment(fA, num_min=10, runs=5):
    trs = []
    num_ms = num_min * 60 * 1000  # in ms
    for i in range(runs):
        print("Run", i + 1)
        try:
            exp = Experiment(duration=num_ms)
            exp.initialize_multisensory(high_freq=fA)
            exp.run_multisensory()
            tr = analyze(exp.get_trials(), plot=False)
            trs.append(tr)
        except:
            print("Could not complete run")

    if len(trs) == 0:
        trs = [0] * runs
    return trs

# Compare influence of fA on amount of temporal recalibration
def compare_freqs(freqs=[15,20,25,30]):
    freq_obs = []
    freq_mean = []
    freq_sd = []

    for freq in freqs:
        print("-----\nFreq:", freq)

        trs = run_experiment(fA=freq)
        freq_mean.append(np.mean(trs))
        freq_sd.append(np.std(trs))
        freq_obs.append(freq)

    plt.figure()
    plt.bar(x=freq_obs, height=freq_mean, yerr=freq_sd)
    plt.xlabel("fA (Hz)")
    plt.ylabel("temporal recalibration (ms)")

    plt.show(block=False)