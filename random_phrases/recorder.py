# -*- coding: utf-8 -*-
"""
Created on Sat Feb 29 13:31:28 2020

@author: Alex Vosk
"""

from pylsl import StreamInlet, resolve_stream
import numpy as np
import time
#from queue import Queue
from progress.bar import Bar
import h5py
from threading import Thread
from os import makedirs


class Recorder():
    def __init__(self, q):
        
        # initialize basic configuration
        self.q_from_display_to_recorder = q
        
        self.srate = 4096
        # variables, changed by commands form q
        
        self.channel_sample = 69
        self.channel_index = 70
        self.dataset_width = 70
        
        # inlet_state:
        # 0 - recording disabled
        # 1 - recording enabled
        self.inlet_state = 1
        
        
        #self.patient_state_paused = -1
        
        # initialize memort variables
        self.memory = []
        
        
        self.phrase = 0
        self.index = 0
        
        # 
        self.patient_state = 0
        self.picture_index = 0      
        
        # resolve lsl stream
        self.stream_name = 'EBNeuro_BePLusLTM_192.168.171.81'
        
        streams = resolve_stream('name', self.stream_name)
        self._printm('Resolving stream \'{}\', {} streams found'.format(self.stream_name, len(streams)))
        self.inlet = StreamInlet(streams[0], self.srate)
        self._printm('Stream resolved')

        self.thread = Thread(target=self.record, args=())
        #self.thread.daemon = True
        
    def start(self):
        self.thread.start()


    def record(self):
        self._printm('Start recording, if \'Recording...\' progress bar is not filling, check lsl input stream')
        self._resolve_q()
    

        with Bar('Recording...', max=1000) as bar:
            while self.inlet_state:
                if not self.inlet_state:
                    print('stop')

                self._resolve_q()
                sample, timestamp = self.inlet.pull_sample()
                if bar.index < 999:
                    bar.next()
                elif bar.index == 999:
                    bar.next()
                    bar.finish()

                # if timestamp exists, add sample to the cache
                if timestamp:
                    appendix = np.asarray(self.index)[np.newaxis]
                    big_sample = np.concatenate([sample, appendix], axis=0)
                    # big_sample = np.zeros(self.dataset_width)
                    # add ecog data
                    # big_sample[0:self.channel_sample] = np.asarray(sample)
                    # add timestemp
                    # big_sample[self.channel_index-1] = self.index
                    self.index = 0

                    # put big_sample into the memory
                    self.memory.append(big_sample)
        print(len(self.memory))
        self._printm('Stop recording')
        t = time.time()
        self._save()
        self._printm('Data saved: {}s:'.format(time.time()-t))

    def _save(self):
        self._printm('is it work?')
        t = time.strftime('%H-%M-%S')
        date = time.strftime('20%y-%m-%d')
        
        experiment_path = 'C:/PatientData/' + date + '/'
        makedirs(str(experiment_path), exist_ok=True)
        
        experiment_file = t + '.h5'
        with h5py.File(experiment_path + experiment_file, 'w') as file:
            if len(self.memory) > 0:
                stacked_data = np.vstack(self.memory)
                file['raw_data'] = stacked_data
                self._printm('Saved {}'.format(stacked_data.shape))
            else:
                empty_shape = (0, self.dataset_width)
                file.create_dataset('raw_data', empty_shape)
                self._printm('Saved {}'.format(empty_shape))
            file.create_dataset('fs', data=self.srate)
            
    # resolve commands from Display object to navigate recording of data
    def _resolve_q(self):
        while not self.q_from_display_to_recorder.empty():
            key, value = self.q_from_display_to_recorder.get()
            if key == 'inlet_state':
                self.inlet_state = value
            elif key == 'index':
                self.index = value


    def _printm(self, message):
        print('{} {}: '.format(time.strftime('%H:%M:%S'), type(self).__name__) + message)


if __name__ == '__main__':
    from queue import Queue
    q = Queue()
    r = Recorder(q)
    r.start()
    time.sleep(5)
    q.put(('inlet_state', 0))

    








