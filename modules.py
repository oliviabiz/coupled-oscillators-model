import numpy as np

# Base oscillator
class Module:
    CONSTANT = 1 / 360

    # frequency: in Hertz (cycles/sec)
    def __init__(self, name, frequency, phase=0, amplitude=1):
        self.name = name
        self.initial_freq = frequency
        self.freq_hertz = frequency
        self.amplitude = amplitude
        self.phase = phase  # initial phase DELAY from 0
        self.period = 360
        self.phase_shifts = 0
        self.angle = 0
        self.inhibition = -1

    def get_name(self):
        return self.name

    def set_frequency(self, freq):
        self.freq_hertz = freq

    def get_period(self):
        return self.period

    def get_amplitude(self):
        return self.amplitude

    def get_phase(self):
        return self.phase

    def get_angle(self):
        return self.angle

    # Resets oscillator to minimum inhibition
    def reset(self):
        self.angle = 270

    def set_angle(self, angle):
        self.angle = angle

    def is_min(self):
        return round(self.angle) == 270
        # return self.near_min()

    def get_inhibition(self):
        return self.inhibition

    # Update oscillator by 1 time step
    def pulse(self):
        y = (
            self.amplitude * (np.sin(2 * np.pi * Module.CONSTANT * self.angle))
            + self.amplitude
        ) / 2
        self.angle += self.freq_hertz
        self.angle = self.angle % 360

        # self.history.append(y)
        self.inhibition = y
        return y, self.angle

    def reset_initial(self):
        self.freq_hertz = self.initial_freq
        self.period = 360
        self.phase_shifts = 0


class M0(Module):
    def __init__(self, name, frequency, phase=0, amplitude=1):
        super().__init__(name, frequency, phase, amplitude)
        self.missed_inputs = 0

    def pulse(self, feedback_m2=0):
        y = (
            self.amplitude * (np.sin(2 * np.pi * Module.CONSTANT * self.angle))
            + self.amplitude
        ) / 2
        if feedback_m2 != 1:
            self.angle += self.freq_hertz
            self.angle = self.angle % 360
        return y, self.angle

    def receive_pulse(self, stimulus, feedback_m2):
        y, x = self.pulse(feedback_m2)

        # two possible sources of error:
        # (+1) unexpected input
        # (-1) expectation unmet
        if stimulus == 1 and round(x) != 270:
            err = 1
        elif round(x) == 270 and stimulus != 1:
            err = -1
        else:
            err = 0

        if stimulus == 1:
            self.missed_inputs = 0

        # err = y

        return y, x, err, stimulus

    def receive_feedback(self, feedback):
        # if unexpected input
        if feedback == 1:
            self.phase_shifts += 1
            if self.phase_shifts > 1:
                new_period = (
                    90 + self.angle + self.missed_inputs * 360
                ) / self.freq_hertz
                new_freq = 360 / new_period
                self.freq_hertz = new_freq
                self.period = new_period

            self.reset()

        # if expectation unmet
        elif feedback == -1:
            self.missed_inputs += 1

    def reset_initial(self):
        super().reset_initial()
        self.missed_inputs = 0


class M0_nested(Module):
    def __init__(self, name, frequency, phase=0, amplitude=1, high_freq=12):
        super().__init__(name, frequency, phase, amplitude)
        self.missed_inputs = 0

        # to add bursts
        self.high_freq = high_freq
        self.nested = Module("burst", self.high_freq, amplitude=0.3)
        self.burst_pos = 0

    def pulse(self, feedback_m2=0):
        y = (
            self.amplitude * (np.sin(2 * np.pi * Module.CONSTANT * self.angle))
            + self.amplitude
        ) / 2
        if feedback_m2 != 1:
            self.angle += self.freq_hertz
            self.angle = self.angle % 360

        b_y, b_x = self.nested.pulse()
        b_y = b_y - (self.nested.amplitude / 2)

        y += b_y
        self.burst_pos = self.burst_pos + 1

        return y, self.angle

    def receive_pulse(self, stimulus, feedback_m2):
        y, x = self.pulse(feedback_m2)

        # two possible sources of error:
        # (+1) unexpected input
        # (-1) expectation unmet
        if stimulus == 1 and round(x) != 270:
            err = 1
        elif round(x) == 270 and stimulus != 1:
            err = -1
        else:
            err = 0

        return y, x, err, stimulus

    def receive_feedback(self, feedback):
        # if unexpected input
        if feedback == 1:
            self.phase_shifts += 1
            if self.phase_shifts > 1:
                new_period = (
                    90 + self.angle + self.missed_inputs * 360
                ) / self.freq_hertz
                new_freq = 360 / new_period
                self.freq_hertz = new_freq
                self.period = new_period

            self.reset()

        # if expectation unmet
        elif feedback == -1:
            self.missed_inputs += 1

    def reset_initial(self):
        super().reset_initial()
        self.missed_inputs = 0


class M0_nested_phasemod(Module):
    def __init__(self, name, frequency, phase=0, amplitude=1, high_freq=12):
        super().__init__(name, frequency, phase, amplitude)
        self.missed_inputs = 0

        # to add bursts
        self.high_freq = high_freq
        self.nested = Module("burst", self.high_freq, amplitude=0.5)
        # self.burst_duration = burst_duration
        self.burst_pos = 0
        # preferred phase: when nested oscillation will have peak amplitude
        self.pref_phase = 90

    def pulse(self, feedback_m2=0):
        y = (
            self.amplitude * (np.sin(2 * np.pi * Module.CONSTANT * self.angle))
            + self.amplitude
        ) / 2
        if feedback_m2 != 1:
            self.angle += self.freq_hertz
            self.angle = self.angle % 360

        b_y, b_x = self.nested.pulse()
        b_y = b_y - (self.nested.amplitude / 2)

        scale = 1 - (abs(self.pref_phase - self.angle) / 180)

        b_y *= scale

        # y += b_y
        y -= abs(b_y)
        self.burst_pos = self.burst_pos + 1

        return y, self.angle

    def receive_pulse(self, stimulus, feedback_m2):
        y, x = self.pulse(feedback_m2)

        # two possible sources of error:
        # (+1) unexpected input
        # (-1) expectation unmet
        if stimulus == 1 and round(x) != 270:
            err = 1
        elif round(x) == 270 and stimulus != 1:
            err = -1
        else:
            err = 0

        return y, x, err, stimulus

    def receive_feedback(self, feedback):
        # if unexpected input
        if feedback == 1:
            self.phase_shifts += 1
            if self.phase_shifts > 1:
                new_period = (
                    90 + self.angle + self.missed_inputs * 360
                ) / self.freq_hertz
                new_freq = 360 / new_period
                self.freq_hertz = new_freq
                self.period = new_period

            self.reset()

        # if expectation unmet
        elif feedback == -1:
            self.missed_inputs += 1

    def reset_initial(self):
        super().reset_initial()
        self.missed_inputs = 0

class subM1(Module):
    def __init__(self, name, frequency, phase=0, amplitude=1):
        super().__init__(name, frequency, phase=phase, amplitude=amplitude)
        self.entrained = False
        self.missed_inputs = 0

    def reset_initial(self):
        super().reset_initial()
        self.entrained = False
        self.missed_inputs = 0

    def calc_error(self):
        error = 0.25 * (
                (
                    self.amplitude
                    * (np.sin(2 * np.pi * Module.CONSTANT * self.angle))
                    + self.amplitude
                )
                / 2
        )
        return error
    
    def pulse(self, stimulus):
        err = 0
        if stimulus:
            err = self.calc_error()
            self.reset()

        y, x = super().pulse()
        return y, err


class M1(Module):
    def __init__(
        self, name, frequency, phase=0, amplitude=1, burst_freq=12, burst_duration=50
    ):
        super().__init__(name, frequency, phase, amplitude)
        self.subm1a = subM1("m1-A", frequency)
        self.subm1b = subM1("m1-B", frequency)
        self.missed_inputs = 0

        # to add bursts
        self.burst_freq = burst_freq
        self.burster = Module("burst", burst_freq, amplitude=0.5)
        self.burst_duration = burst_duration
        self.burst_pos = 0
        self.bursting = False

    def receive_error(self, err, stimulus, m0_angle, m0frequency):
        feedback = err
        y, x = super().pulse()

        # positive error, unexpected input
        if feedback == 1:
            self.bursting = True
            # equivalent to phase_shifts of M0
            self.phase_shifts += 1
            if self.phase_shifts > 1:  # adjust frequency
                new_period = (90 + m0_angle + (self.missed_inputs * 360)) / m0frequency
                new_freq = 360 / new_period

                # if new frequency appeared in inputs, entrain subM1A, if it's not already
                if not self.subm1a.entrained:
                    self.subm1a.period = new_period
                    self.subm1a.freq_hertz = new_freq
                    self.subm1a.entrained = True
                    self.subm1b.period = new_period
                    self.subm1b.freq_hertz = new_freq
                # if subM1A is entrained but new frequency in inputs, entrain subM1B
                elif not self.subm1b.entrained:
                    self.subm1b.period = new_period
                    self.subm1b.freq_hertz = new_freq
                    self.subm1b.entrained = True

            self.missed_inputs = 0

        # expected input, found none. keep track but otherwise change nothing
        elif feedback == -1:
            self.missed_inputs = self.missed_inputs + 1

        # take care of bursting
        if self.bursting and self.burst_pos < self.burst_duration:
            b_y, b_x = self.burster.pulse()
            b_y = b_y - (self.burster.amplitude / 2)
            y += b_y
            self.burst_pos = self.burst_pos + 1

        if self.burst_pos >= self.burst_duration:
            self.burst_pos = 0
            self.bursting = False

        return y, x, feedback, stimulus

    def reset_initial(self):
        super().reset_initial()
        self.missed_inputs = 0


class M2(Module):
    def __init__(
        self,
        name,
        frequency,
        m0,
        m1,
        submodules,
        phase=0,
        amplitude=1,
        burst_freq=12,
        burst_duration=50,
    ):
        super().__init__(name, frequency, phase, amplitude)
        self.value = 0
        self.duration = self.get_period()
        self.Aduration = 0
        self.Bduration = 0
        self.threshold = 3
        self.m0 = m0
        self.m1 = m1
        self.subA, self.subB = submodules
        self.pattern = [0]
        self.time = [self.period]
        self.i = 0

        # Take care of bursting
        self.burster = Module("burst", burst_freq, amplitude=0.5)
        self.burst_duration = burst_duration
        self.burst_pos = 0
        self.bursting = False

    def pulse(self):
        y = self.pattern[self.i]
        self.value = self.pattern[self.i]
        self.angle += self.freq_hertz

        if self.angle > round(self.time[self.i]):
            self.i += 1
            self.i = self.i % len(self.pattern)
            self.angle = self.angle % self.duration
        return y, self.angle

    def send_feedback(self):
        # output 1 if m0 should reset i.e. if the submodule it's listening to is at / nearing a minimum
        # output 0 otherwise
        feedback = 0

        # If currently listening to subM1A and it's at a minimum
        if self.value == 1 and self.subA.is_min():
            feedback = 1
            self.m0.reset()

        # If currently listening to subM1B and it's at a minimum
        if self.value == -1 and self.subB.is_min():
            feedback = 1
            self.m0.reset()

        return feedback

    def receive_feedback(self, feedback, stimulus):
        y, x = self.pulse()

        # When subM1a first becomes entrained
        if stimulus == 1 and self.value == 0 and self.subA.entrained:
            self.value = 1
            self.Aduration = 360 / self.subA.freq_hertz
            self.duration = self.Aduration
            self.pattern = [1]
            self.time = [self.Aduration]

        # When subM1b becomes entrained
        if self.Bduration == 0 and self.subB.entrained:
            self.Bduration = 360 / self.subB.freq_hertz

        # Build the pattern
        if stimulus == 1:
            # If listening to M1A
            if self.value == 1:
                # If M1A is at a minimum, at another M1A to the pattern
                if self.subA.is_min() and self.pattern.count(-1) == 0:
                    self.duration += self.Aduration
                    self.pattern.append(1)
                    self.time.append(self.time[-1] + self.Aduration)
                    self.angle = 0
                    self.i = 0

                # Else, add M1B
                elif not self.subA.is_min() and self.subB.entrained:
                    self.duration += self.Bduration
                    self.pattern.append(-1)
                    self.time.append(self.time[-1] + self.Bduration)
                    self.angle = 0
                    self.i = 0

        # Check missed inputs subM1a
        if self.value == 1 and self.subA.is_min():
            self.bursting = True
            if stimulus == 0:
                self.subA.missed_inputs += 1
            elif stimulus == 1:
                self.subA.missed_inputs = 0

        # Check missed inputs subM1b
        if self.value == -1 and self.subB.is_min():
            self.bursting = True
            if stimulus == 0:
                self.subB.missed_inputs += 1
            elif stimulus == 1:
                self.subB.missed_inputs = 0

        # If # of missed inputs exceeds threshold, reset all modules
        if (
            self.subA.missed_inputs >= self.threshold
            or self.subB.missed_inputs >= self.threshold
        ):
            self.m1.reset_initial()
            self.subA.reset_initial()
            self.subB.reset_initial()
            self.reset_initial()
            self.m0.reset_initial()

        # take care of bursting
        if self.bursting and self.burst_pos < self.burst_duration:
            b_y, b_x = self.burster.pulse()
            b_y = b_y - (self.burster.amplitude / 2)
            y += b_y
            self.burst_pos = self.burst_pos + 1

        if self.burst_pos >= self.burst_duration:
            self.burst_pos = 0
            self.bursting = False

        return y, x

    def reset_initial(self):
        self.pattern = [0]
        self.time = [360]
        self.i = 0
        self.value = 0
        self.duration = 360
        self.Aduration = 0
        self.Bduration = 0



class Sensory(Module):
    def __init__(self, name, frequency, phase=0, amplitude=1, fA=12, fP=270):
        super().__init__(name, frequency, phase, amplitude)

        self.bursting = False
        self.current_burst = 0
        self.slot_count = 0

        # Define sensory registration slots
        self.burst_phase = fP
        self.burst_freq = fA
        self.max_slots = 5
        self.burst_duration =  round(360 // fA)

        self.burster = Module(
            "burst", frequency=self.burst_freq, amplitude=0.5, phase=180
        )
        self.burster.set_angle(180)

    # Shifts preferred phase of bursts along slow wave cycle by sign cycles of fast bursts
    def adjust_phase(self, sign):
        if sign != 0:
            ratio = (self.burst_duration / self.period) * 360
            self.burst_phase += ratio * sign
            self.burst_phase %= 360
            self.burst_phase = round(self.burst_phase)

    def reset_fastphase(self):
        cycle_degrees = (self.burst_duration / self.period) * 360
        self.burst_phase = self.angle - (round(self.max_slots * cycle_degrees / 2, 0))

    # Resets slot counter (exit burst mode)
    def reset_slots(self):
        self.bursting = False
        self.slot_count = 1
        self.current_burst = 0

    def pulse(self, stimulus):
        y, x = super().pulse()
        self.angle = x
        reg = 0
    
        # enter bursting mode
        if not self.bursting and (round(self.angle) == self.burst_phase):
            self.bursting = True
            self.slot_count = 1
            self.current_burst = 0

        # get rank number
        if stimulus and self.bursting:
            reg = self.slot_count

        if self.bursting:
            if self.current_burst == self.burst_duration:
                self.current_burst = 0
                self.slot_count += 1
                if self.slot_count > self.max_slots:
                    self.reset_slots()
                    return y, reg
        
            b_y, _ = self.burster.pulse()
            b_y = b_y - self.burster.get_amplitude() / 2
            y += b_y

            self.current_burst += 1
            

        return y, reg  # amplitude and slot in which input was registered, if at all

# Integrator
class M3(Module):
    def __init__(self, name, frequency=10, phase=0, amplitude=1):
        super().__init__(name, frequency, phase, amplitude)
        self.calibrating = False
        self.calibBegin = None
        self.recal = None

    def pulse(self, reg1, reg2):
        y, x = super().pulse()
        y -= self.amplitude / 2  # oscillate around 0

        # Attempt to bind inputs
        if reg1 == reg2 and reg1 != 0:
            sync = 1
        else:
            sync = -1

        # Determine if (and how much) recalibration is required
        recal = reg1 - reg2


        # Begin recalibration pulse
        if recal != 0:
            self.calibrating = True
            self.calibBegin = round(self.get_angle())
            self.recal = recal * 2
            return y, x, sync, recal

        # Amplitude modulated by magnitude of recalibration
        if self.calibrating:
            y *= abs(self.recal)

        # End recalibration pulse after 1 cycle
        if round(self.get_angle()) == self.calibBegin:
            self.calibrating = False
            self.calibBegin = None
            self.recal = None

        return y, x, sync, recal