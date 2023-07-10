from inputs import *
from modules import *

""" Functions to create different types of inputs """

class Results:
    def __init__(self):
        self.results = {}
    
    def add(self, result, result_name):
        if result_name not in self.results.keys():
            self.results[result_name] = result

    def get(self, result_name):
        return self.results[result_name]
    
    def list_results(self):
        return self.results.keys()
    
class Experiment:
    # Initialize necessary modules
    def __init__(self, duration):
        self.duration = duration
        self.result = Results()
        self.trials = list()

    def create_stimuli(self, stim_intervals):
        self.time, self.stim, _ = pattern(self.duration, stim_intervals)
        self.result.add(self.time, "time")

    def end(self, end_time=1000):
        self.stim[end_time:] = 0

    def create_multisensory_stim(self,modalities=2):
        stimuli, trial_start, trial_end, leads, soas = multisensory_stimuli(self.duration, modalities)
        self.stim = stimuli
        self.trial_start = trial_start
        self.trial_end = trial_end
        self.leads = leads
        self.soas = soas
        self.time = np.linspace(0, self.duration, self.duration, endpoint=False)
        self.result.add(self.time, "time")

    def initialize_modules(self, m0_class = M0):
        self.m0 = m0_class("m0", frequency=1)
        self.m1 = M1("m1", frequency=1)
        self.m2 = M2("m2", frequency=1, m0=self.m0, m1=self.m1, submodules=[self.m1.subm1a, self.m1.subm1b])

    def initialize_multisensory(self, low_freq = 1, high_freq = 12):
        self.audio = Sensory("audio", frequency = low_freq, fA=high_freq)
        self.visual = Sensory("visual", frequency = low_freq, fA=high_freq)
        self.integrator = M3("integrator", frequency = low_freq * 4)


    def get_results(self):
        return self.result
    
    def get_trials(self):
        return self.trials
    
    def initialize_timeseries(self, num_series):
        return [np.zeros((self.duration,)) for _ in range(num_series)]

    # Returns error incurred by m2 prediction
    def calculate_error(self, m2_feedback):
        err_pred = 0
        if m2_feedback == 1:
            err_pred = 0.5 * (
                (
                    self.m0.amplitude * (np.sin(2 * np.pi * Module.CONSTANT * self.m0.angle))
                    + self.m0.amplitude
                )
                / 2
            )
        return err_pred
    
    def register_trial(self, trial_lead, trial_soa, trial_sync):
        self.trials.append({"lead": trial_lead, "soa": trial_soa, "response": trial_sync})
 
    # Run experiment (temporal recalibration)
    def run_multisensory(self):
        assert hasattr(self, "audio"), "Must initialize multisensory modules"
        assert hasattr(self, "visual"), "Must initialize multisensory modules"
        assert hasattr(self, "integrator"), "Must initialize multisensory modules"

        series = self.initialize_timeseries(6)
        y_a, y_v, y_i, recal, sync, cost = series


        self.create_multisensory_stim()
        stim_a, stim_v = self.stim
      
        stim_a_reg = np.zeros(stim_a.shape)
        stim_v_reg = np.zeros(stim_v.shape)

        stim_a_reg = stim_a
        stim_v_reg = stim_v

        last_a = 0
        last_v = 0

        for i in range(self.duration):
            if i in self.trial_start:  # beginning of trial
                trial_num = np.where(self.trial_start == i)[0][0]

            a0, reg_a = self.audio.pulse(stim_a_reg[i])

            v0, reg_v = self.visual.pulse(stim_v_reg[i])
            # i0, _, recalInt = self.integrator.pulse(reg_a, reg_v)
            i0, _, _, recalInt = self.integrator.pulse(0,0)
            if recalInt != 0:
                print("Recal returned by M3", recalInt)

            if last_a == 0 and reg_a != 0:
                last_a = reg_a
            if last_v == 0 and reg_v != 0:
                last_v = reg_v

            if i in self.trial_end:  # reset "counter
                i0, _, syncInt, recalInt = self.integrator.pulse(last_a, last_v)
        
                trial_num = np.where(self.trial_end == i)[0][0]
                recal[i] = recalInt
                sync[i] = syncInt

                if last_a == 0 and last_v == 0: 
                    # ! Input missed by both modules
                    # * Solution: Shift slow phase (reset to 0) and adjust fast burst to center minimum
                    for mod in [self.audio, self.visual]:
                        mod.reset()
                        mod.reset_fastphase()


                last_a = 0
                last_v = 0

                # Record trial info
                self.register_trial(self.leads[trial_num], self.soas[trial_num], sync[i])

                # Recalibrate
                self.audio.adjust_phase(recal[i])
               
            y_a[i] = a0
            y_v[i] = v0
            y_i[i] = i0

        self.result.add(stim_a, self.audio.name)
        self.result.add(stim_v, self.visual.name)
        self.result.add(y_i, self.integrator.name)
        self.result.add(y_a, "audio module")
        self.result.add(y_v, "visual module")
        self.result.add(recal, "recalibration")
        self.result.add(sync, "synchrony")


    # Run regular experiment (neural entrainment)
    def run(self):
        if (not hasattr(self, "stim") and hasattr(self, "time")):
            raise Exception("Must create stimulus before running experiment")


        if not( hasattr(self, 'm0') and hasattr(self, 'm1') and hasattr(self, 'm2')):
            raise Exception("Must initialize modules before running experiment")

        series = self.initialize_timeseries(8)
        x, cost, total_cost, y, ym1, ym1a, ym1b, ym2 = series

        for i in range(self.duration):
            feedback_m2 = self.m2.send_feedback()
            err_pred = self.calculate_error(feedback_m2)
        
            y[i], x[i], err0, stimulus = self.m0.receive_pulse(self.stim[i], feedback_m2)
            ym1[i], _, feedback, stimulus = self.m1.receive_error(
                err0, stimulus, self.m0.angle, self.m0.freq_hertz
            )

            self.m0.receive_feedback(feedback)

            ym2[i], _ = self.m2.receive_feedback(feedback, stimulus)

            ym1a[i], err_m1a = self.m1.subm1a.pulse(stimulus)
            ym1b[i], err_m1b = self.m1.subm1b.pulse(stimulus)

            cost[i] = err_pred + err_m1a + err_m1b
            if err0 != 0:
                cost[i] += y[i]
            total_cost[i:] += cost[i]
  
        self.result.add(self.stim, "stim")
        self.result.add(y, self.m0.name)
        self.result.add(ym1, self.m1.name)
        self.result.add(ym1a, self.m1.subm1a.name)
        self.result.add(ym1b, self.m1.subm1b.name)
        self.result.add(ym2, self.m2.name)
        self.result.add(cost, "cost")
        self.result.add(total_cost, "total cost")