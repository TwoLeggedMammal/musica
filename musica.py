import pygame, numpy, math

class Mixer(object):
    # Controls the playback of all of our sounds
    sample_rate = 22050
    bits = 16
    max_sample = 2**(bits - 1) - 1  # the range of our sound array values, a signed 16-bit int
    notes = []

    def __init__(self, sample_rate=22050, bits=16, channels=1):
        self.sample_rate = sample_rate
        self.bits = bits
        self.max_sample = 2**(bits - 1) - 1
        pygame.mixer.init(frequency=sample_rate, size=-bits, channels=channels)

    def play(self, buffer):
        sound = pygame.sndarray.make_sound(buffer)
        sound.play()
        pygame.time.wait(int(round((float(buffer.size) / float(self.sample_rate)) * float(1000))))

    def queue(self, buffer):
        self.notes.append(buffer)

    def play_queue(self):
        for note in self.notes:
            sound = pygame.sndarray.make_sound(note)
            sound.play()
            pygame.time.wait(int(round((float(note.size) / float(self.sample_rate)) * float(1000))))            

    def close(self):
        pygame.mixer.quit()


class Sound(object):
    mixer = None
    
    # Our C-major scale. We can multiply by powers of 2 to get to any octave we need.
    notes = {
        'c': 261.63,
        'd': 293.66,
        'e': 329.63,
        'f': 349.23,
        'g': 392.0,
        'a': 440,
        'b': 493.88
    }

    def __init__(self, mixer):
        self.mixer = mixer

    def add_attack(self, buf, duration):
        # Quickly ramp up the volume at the beginning of the note.
        # Default duration is 0.1 seconds
        for i, val in enumerate(buf[0:int(duration * float(self.mixer.sample_rate))]):
            strength = float(i) / (float(self.mixer.sample_rate) * duration)
            buf[i] = val - (val * (1 - strength))

        return buf

    def add_vibrato(self, buf, speed, strength):
        # Scrunch up the sound wave at periodic intervals so that the pitch wavers up and down
        # Speed is how frequently we are at the base pitch. 0.2s is reasonable.
        # Strength is how much the pitch varies. Should be low, maybe 0.15
        if speed <= 0:
            return buf

        original = numpy.copy(buf)
        speed = speed * self.mixer.sample_rate
        for i, val in enumerate(buf):
            diff = int(((abs((i % speed) - (speed / 2))) - (speed / 4)) * strength)

            if i + diff >= 0 and i + diff < buf.size:
                buf[i] = original[i + diff]
        return buf

    def add_fade(self, buf, strength):
        # Makes the note lose volume over time, down to the final strength.
        # Strength 0 makes it fade out completely by the end, 0.5 puts it at half volume.
        for i, val in enumerate(buf):
            buf[i] = val - (val * strength * (math.pow(float(i) / float(buf.size), 2)))

        return buf

    def adjust_volume(self, buf, strength):
        # Multiplies the volume of the entire sound by the strength from 0 to 1 (full volume) or higher increased volume.
        # High values can cause clipping.
        for i, val in enumerate(buf):
            buf[i] = val - (val * (1 - strength))

        return buf

    def add_static(self, buf, strength):
        # Replaces random samples of the sound with random values and creates a staticy sound.
        # Strength should be low. .002 is an old timey record, 1.0 is white noise.
        random_chance = numpy.random.random_sample((buf.size,))
        random_values = numpy.random.random_sample((buf.size,)) * self.mixer.max_sample
        for i, val in enumerate(buf):
            if random_chance[i] < strength:
                buf[i] = int(random_values[i])

        return buf

    def generate(self, 
                pitch, 
                duration=1, 
                vibrato=0.00, 
                vibrato_speed=0.2, 
                volume=1, 
                static=0.0,
                fade = 0.3,
                attack=0.05):        
        n_samples = int(round(duration*float(self.mixer.sample_rate)))
        buf = numpy.zeros(n_samples, dtype = numpy.int16)
        
        # Generate a pure sin wave at the desired frequency
        for s in range(n_samples):
            t = float(s) / self.mixer.sample_rate
            buf[s] = int(self.mixer.max_sample * math.sin(math.pi * pitch * t))

        # Run the sample through all of our filters in this order
        buf = self.adjust_volume(buf, volume)
        buf = self.add_attack(buf, attack)
        buf = self.add_vibrato(buf, vibrato_speed, vibrato)
        buf = self.add_fade(buf, fade)
        buf = self.add_static(buf, static)

        return buf

def ode_to_joy(mixer, sound):
    print 'generating joy...'
    # verse 1, quieter and old timey
    mixer.queue(sound.generate(sound.notes['e'] * 2, volume=0.5, duration=0.5, static=0.002))
    mixer.queue(sound.generate(sound.notes['e'] * 2, volume=0.5, duration=0.5, static=0.002))    
    mixer.queue(sound.generate(sound.notes['f'] * 2, volume=0.5, duration=0.5, static=0.002))    
    mixer.queue(sound.generate(sound.notes['g'] * 2, volume=0.5, duration=0.5, static=0.002))
    mixer.queue(sound.generate(sound.notes['g'] * 2, volume=0.5, duration=0.5, static=0.002))
    mixer.queue(sound.generate(sound.notes['f'] * 2, volume=0.5, duration=0.5, static=0.002))
    mixer.queue(sound.generate(sound.notes['e'] * 2, volume=0.5, duration=0.5, static=0.002))
    mixer.queue(sound.generate(sound.notes['d']*2, volume=0.5, duration=0.5, static=0.002))
    mixer.queue(sound.generate(sound.notes['c']*2, volume=0.5, duration=0.5, static=0.002))
    mixer.queue(sound.generate(sound.notes['c']*2, volume=0.5, duration=0.5, static=0.002))
    mixer.queue(sound.generate(sound.notes['d']*2, volume=0.5, duration=0.5, static=0.002))
    mixer.queue(sound.generate(sound.notes['e'] * 2, volume=0.5, duration=0.5, static=0.002))
    mixer.queue(sound.generate(sound.notes['e'] * 2, volume=0.5, duration=0.75, static=0.002))
    mixer.queue(sound.generate(sound.notes['d'] * 2, volume=0.5, duration=0.25, static=0.002))
    mixer.queue(sound.generate(sound.notes['d'] * 2, volume=0.5, duration=1.0, static=0.002))
    # verse 2, louder and more natural instrument sounding
    mixer.queue(sound.generate(sound.notes['e'] * 2, volume=0.7, duration=0.5, fade=1.0))
    mixer.queue(sound.generate(sound.notes['e'] * 2, volume=0.7, duration=0.5, fade=1.0))    
    mixer.queue(sound.generate(sound.notes['f'] * 2, volume=0.7, duration=0.5, fade=1.0))    
    mixer.queue(sound.generate(sound.notes['g'] * 2, volume=0.7, duration=0.5, fade=1.0))
    mixer.queue(sound.generate(sound.notes['g'] * 2, volume=0.7, duration=0.5, fade=1.0))
    mixer.queue(sound.generate(sound.notes['f'] * 2, volume=0.7, duration=0.5, fade=1.0))
    mixer.queue(sound.generate(sound.notes['e'] * 2, volume=0.7, duration=0.5, fade=1.0))
    mixer.queue(sound.generate(sound.notes['d']*2, volume=0.7, duration=0.5, fade=1.0))
    mixer.queue(sound.generate(sound.notes['c']*2, volume=0.7, duration=0.5, fade=1.0))
    mixer.queue(sound.generate(sound.notes['c']*2, volume=0.7, duration=0.5, fade=1.0))
    mixer.queue(sound.generate(sound.notes['d']*2, volume=0.7, duration=0.5, fade=1.0))
    mixer.queue(sound.generate(sound.notes['e'] * 2, volume=0.7, duration=0.5, fade=1.0))
    mixer.queue(sound.generate(sound.notes['d'] * 2, volume=0.7, duration=0.75, fade=1.0))
    mixer.queue(sound.generate(sound.notes['c'] * 2, volume=0.7, duration=0.25, fade=1.0))
    mixer.queue(sound.generate(sound.notes['c'] * 2, volume=0.7, duration=1.0, fade=1.0))
    print 'playing back'
    mixer.play_queue()


mixer = Mixer()
sound = Sound(mixer)

ode_to_joy(mixer, sound)
mixer.close()



