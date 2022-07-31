# -*- coding: utf-8 -*-
"""
Created on Thu Feb 10 12:36:33 2022

@author: AlexVosk
"""
import os
import sys
import time
import re
import copy
import random

import codecs
import numpy as np

from PIL import ImageFont, ImageDraw, Image
import PIL.ImageQt as ImageQt
import PyQt5
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QDesktopWidget
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5.QtCore import QTimer
# from psychopy import parallel

# import rusyllab
# from russian_g2p.Accentor import Accentor
# from russian_g2p.Grapheme2Phoneme import Grapheme2Phoneme

from queue import Queue
# from recorder import Recorder
# from triggerbox import Triggerbox

WINDOW_X = 1920
WINDOW_Y = 1080
back_ground_color = (0,0,0)
font_size = 64
font_color = (255,255,255)
unicode_font = ImageFont.truetype("DejaVuSans.ttf", font_size)
X, Y = 240, 70
phrase_center = 4
extra_length = 4


def estimate_phrases(phrases):
    lines = []
    phrases_length_max = np.max([len(phrase)for phrase in phrases])
    #lines = ['|'.join(phrase) for phrase in phrases]

    word_X_max, word_Y_max = 0, 0
    for phrase in phrases:
        for word in phrase:
            text_size = unicode_font.getsize(word)
            word_X_max = np.max([word_X_max, text_size[0]])
            word_Y_max = np.max([word_Y_max, text_size[1]])
    word_length = word_X_max + 2*extra_length
    word_hight = word_Y_max
    words_coordinates = []
    XY_center = np.asarray([WINDOW_X/2, WINDOW_Y/2])
    for i in range(phrases_length_max):
        xy_left_down = XY_center + np.asarray([word_length*(-phrase_center+i), -word_hight/2])
        xy_right_high = XY_center + np.asarray([word_length*(-phrase_center+i+1), word_hight/2])
        words_coordinates.append(np.concatenate([xy_left_down, xy_right_high]))
    words_coordinates = np.stack(words_coordinates)
    print(words_coordinates)
    return words_coordinates

class Word:
    def __init__(self, word, word_coordinates, font_size):
        self.unicode_font = ImageFont.truetype("DejaVuSans.ttf", font_size)
        #self.max_y_size = self.unicode_font.getsize('у')[1]
        self.word = word
        #self.word_size = self.unicode_font.getsize(self.word)
        x_left_down = word_coordinates[0]
        y_left_down = word_coordinates[1]
        x_right_high = word_coordinates[2]
        y_right_high = word_coordinates[3]
        
        #self.box_size = (X, Y)
        self.position_text = x_left_down + extra_length, y_left_down
        self.position_box1 = x_left_down, y_left_down
        self.position_box2 = x_right_high, y_right_high

def make_slide(words, words_coordinates):
    slide = []
    # words = line.split('|')
    
    for i, word in enumerate(words):
        word_coordinates = words_coordinates[i]
        w = Word(word, word_coordinates, font_size)
        slide.append(w)
        #y_start += Y # unicode_font.getsize(word)[1]

    return slide

def make_pictures(slide):
    pictures = []
    for i, wi in enumerate(slide):
        picture = Image.new ( "RGB", (WINDOW_X, WINDOW_Y), back_ground_color)
        draw = ImageDraw.Draw(picture)
        draw.rectangle((wi.position_box1, wi.position_box2), fill="pink", outline='green')
        draw.text(wi.position_text, wi.word, font=unicode_font, fill=(0,0,0))
        for j, w in enumerate(slide):
            if i!=j:
                draw.rectangle((w.position_box1, w.position_box2), fill="black", outline='green')
                draw.text(w.position_text, w.word, font=unicode_font, fill=font_color)
        pictures.append(picture)
    return pictures



def make_empty_slide(upper_left):
    slide = []
    unicode_font = ImageFont.truetype("DejaVuSans.ttf", font_size)
    max_y_size = unicode_font.getsize('Уу')[1]
    x_start = upper_left[0]
    y_start = upper_left[1]
    words = (['     ']*6)
    for j, word in enumerate(words):
        w = Word(word, x_start, y_start, font_size)
        slide.append(w)
        x_start += np.max([unicode_font.getsize(word+'  ')[0], X])
    return slide



def pil2pixmap(im):
    if im.mode == "RGB":
        r, g, b = im.split()
        im = Image.merge("RGB", (b, g, r))
    elif  im.mode == "RGBA":
        r, g, b, a = im.split()
        im = Image.merge("RGBA", (b, g, r, a))
    elif im.mode == "L":
        im = im.convert("RGBA")
    # Build in RGBA konvertieren, falls nicht bereits passiert
    im2 = im.convert("RGBA")
    data = im2.tobytes("raw", "RGBA")
    qim = QImage(data, im.size[0], im.size[1], QImage.Format_ARGB32)
    pixmap = QPixmap.fromImage(qim)
    return pixmap

def make_pictures_slides_from_phrases(phrases):
    word_coordinates = estimate_phrases(phrases)
    # empty_slide = make_empty_slide(word_coordinates)
    slides = []
    for line in phrases:
        slides.append(make_slide(line, word_coordinates))
    # picture_empty = make_pictures(empty_slide)
    pictures = [make_pictures(slide) for slide in slides]
    return pictures


class App(QWidget):
    def __init__(self, q, phrases, dictionary, n):
        super().__init__()
        self.title = 'PyQt5 Phrases'
        self.left = 10
        self.top = 10
        
        self.q = q

        self.indexes = []
        for phrase in phrases:
            index = []
            for word in phrase:
                if word in dictionary:
                    index.append(dictionary[word])
                else:
                    index.append(0)
            self.indexes.append(index)
        for index in self.indexes:
            print(index)
        
        
        pictures_slides = make_pictures_slides_from_phrases(phrases)
        # self.start_image = [pil2pixmap(picture) for picture in picture_empty]
        self.images = [[pil2pixmap(picture) for picture in pictures_slide] for pictures_slide in pictures_slides]

        
        self.nimages = len(self.images)
        self.nwords = len(self.images[1])
        self.image_counter = 0
        self.word_counter = 0
        
        self.current_index = (0, 0)
        
        self.width = WINDOW_X
        self.height = WINDOW_Y
        
        # self.recorder = Recorder(self.q)
        # self.recorder.start()
        time.sleep(2)
        
        self.q.put(('inlet_state', 1))
        print(('inlet_state', 1))
        time.sleep(3)
        
        self.initUI()


    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.label = QLabel(self)
        timer = QTimer(self)
        self.update_image()

        timer.timeout.connect(self.update_index)
        timer.timeout.connect(self.update_image)
        timer.start(1500)

    def update_index(self):
        if self.image_counter >= self.nimages:
            self.q.put(('inlet_state', 0))
            self.current_index = (0, 0)
            # self.triggerbox.disconnect()
        elif self.image_counter < self.nimages and self.word_counter < self.nwords:
            self.current_index = (self.image_counter, self.word_counter)
        
        index = self.indexes[self.current_index[0]][self.current_index[1]]
        
        self.q.put(('index', index))
        # self.triggerbox.trigger(text=index)
        #print(self.current_index[0], self.current_index[1], index)
        
        self.word_counter += 1
        if self.word_counter >= self.nwords:
            self.image_counter += 1
            self.word_counter = 0

    def update_image(self):
        pixmap = self.images[self.current_index[0]][self.current_index[1]]
        if not pixmap.isNull():
            self.label.setPixmap(pixmap)
            self.label.adjustSize()
            self.resize(pixmap.size())



def make_order(n=12):
    #np.random.seed(seed)
    order = np.arange(6)
    order_total = []
    while n > 0:
        order_candidate = np.copy(order)
        np.random.shuffle(order_candidate)
        if len(order_total) == 0 or (order_candidate[0] != order_total[-1][-1]):
            order_total.append(order_candidate)
            n -= 1
    return np.concatenate(order_total)
    
def read_words():
    def read_file(filename):
        words = []
        with codecs.open(filename, 'r', encoding='utf-8') as file:
            for line in file.readlines():
                line = line.strip()
                if len(line) > 0:
                    words.append(line)
        return words
    vocabulary, dictionary = {}, {}
    vocabulary['nouns'] = read_file('stimulus/nouns.txt')
    vocabulary['verbs'] = read_file('stimulus/verbs.txt')
    vocabulary['adjs'] = read_file('stimulus/adjs.txt')
    index = 1
    for words in (vocabulary['nouns'], vocabulary['verbs'], vocabulary['adjs']):
        for word in words:
            dictionary[word] = index
            index += 1
    return vocabulary, dictionary

def make_phrases(nphrases, vocabulary):
    nnoun, nverb, nadj = len(vocabulary['nouns']), len(vocabulary['verbs']), len(vocabulary['adjs'])
    assert nphrases % nnoun == 0, 'nphrases should be divisible by {}'.format(nnoun)
    
    def make_phrase_order(nnoun, nverb, nadj, ntypes):
            noun_order_left = np.concatenate([np.arange(nnoun) for _ in range(ntypes)])
            noun_order_right = np.concatenate([(np.arange(nnoun) + i + 1) % 10 for i in range(ntypes)])
            verb_order = np.concatenate([(np.arange(nverb) + int(i*nverb/nnoun)) % nverb for i in range(ntypes * int(nnoun/nverb))])
            adj_order = np.concatenate([(np.arange(nadj) + int(i*nadj/nnoun)) % nadj for i in range(ntypes * int(nnoun/nadj))])
            phrase_order = np.stack((np.arange(nnoun*ntypes), noun_order_left, noun_order_right, verb_order, adj_order)).T
            np.random.shuffle(phrase_order)
            return phrase_order
            
    ntypes = 3
    phrase_order = make_phrase_order(nnoun, nverb, nadj, ntypes)
    phrases = []
    for phrase_indices in phrase_order:
        j = phrase_indices[0] // nnoun
        if j == 0:
            word1 = vocabulary['nouns'][phrase_indices[1]]
            word2 = vocabulary['verbs'][phrase_indices[3]]
            word3 = vocabulary['adjs'][phrase_indices[4]]
            word4 = vocabulary['nouns'][phrase_indices[2]]
        elif j == 1:
            word1 = vocabulary['adjs'][phrase_indices[4]]
            word2 = vocabulary['nouns'][phrase_indices[1]]
            word3 = vocabulary['verbs'][phrase_indices[3]]
            word4 = vocabulary['nouns'][phrase_indices[2]]
        elif j == 2:
            word1 = vocabulary['nouns'][phrase_indices[1]]
            word2 = vocabulary['adjs'][phrase_indices[4]]
            word3 = vocabulary['nouns'][phrase_indices[2]]
            word4 = vocabulary['verbs'][phrase_indices[3]]
        phrase = [word1, word2, word3, word4]
        phrases.append(phrase)
    return phrases
    


if __name__ == '__main__':
    n = 1
    if '-test' in sys.argv:
        n = 10
    elif '-5min' in sys.argv:
        n = 20
    elif '-10min' in sys.argv:
        n = 40

    vocabulary, dictionary = read_words()
    print(vocabulary)
    phrases = make_phrases(n, vocabulary)
    for phrase in phrases:
        print(phrase)
    phrases_hat = [['     ' for _ in range(7)]]
    for phrase in phrases:
        phrase = ['     '] + ['     '] + phrase + ['     ']
        phrases_hat.append(phrase)
    phrases_hat.append(['     ' for _ in range(7)])
    phrases = phrases_hat
    
    q = Queue()
    app = QApplication(sys.argv)
    
    try:
        display_monitor = 1
        monitor = QDesktopWidget().screenGeometry(display_monitor)
    except:
        display_monitor = 0
        monitor = QDesktopWidget().screenGeometry(display_monitor)
    print('display_monitor:', display_monitor)

    ex = App(q, phrases, dictionary, n)
    ex.move(monitor.left(), monitor.top())
    ex.showFullScreen()
    
    ex.show()
    sys.exit(app.exec_())


   