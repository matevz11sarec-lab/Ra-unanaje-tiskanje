import os
import math
import re
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from PIL import Image
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from PyPDF2 import PdfReader

# === CENIKI ===
cenik_gravura = [
    {"min": 1, "max": 25, "dobava": 20, "prodaja": 28},
    {"min": 26, "max": 50, "dobava": 25, "prodaja": 35},
    {"min": 51, "max": 100, "dobava": 30, "prodaja": 42},
    {"min": 101, "max": 150, "dobava": 40, "prodaja": 56},
    {"min": 151, "max": 200, "dobava": 45, "prodaja": 63},
    {"min": 201, "max": 250, "dobava": 50, "prodaja": 70},
    {"min": 251, "max": 300, "dobava": 55, "prodaja": 77},
    {"min": 301, "max": 400, "dobava": 65, "prodaja": 85},
    {"min": 401, "max": 1000, "dobava": 160, "prodaja": 220}
]

cenik_bloki = [
    {"min": 1, "max": 10, "dobava": 30, "prodaja": 42},
    {"min": 11, "max": 20, "dobava": 40, "prodaja": 56},
    {"min": 21, "max": 30, "dobava": 43, "prodaja": 61},
    {"min": 31, "max": 40, "dobava": 45, "prodaja": 63},
    {"min": 41, "max": 49, "dobava": 49, "prodaja": 69},
    {"min": 50, "max": 59, "dobava": 55, "prodaja": 77},
    {"min": 60, "max": 69, "dobava": 66, "prodaja": 93},
    {"min": 70, "max": 79, "dobava": 77, "prodaja": 108},
    {"min": 80, "max": 99, "dobava": 88, "prodaja": 124},
    {"min": 100, "max": 149, "dobava": 110, "prodaja": 154},
    {"min": 150, "max": 9999, "dobava": 165, "prodaja": 231}
]

cenik_vzigalniki = [
    {"min": 1, "max": 50, "dobava": 25, "prodaja": 35},
    {"min": 51, "max": 100, "dobava": 35, "prodaja": 49},
    {"min": 101, "max": 150, "dobava": 45, "prodaja": 63},
    {"min": 151, "max": 200, "dobava": 55, "prodaja": 77},
    {"min": 201, "max": 250, "dobava": 65, "prodaja": 91},
    {"min": 251, "max": 300, "dobava": 75, "prodaja": 105}
]

cenik_vizitke = [
    {"min": 1, "max": 50, "dobava": 15, "prodaja": 21},
    {"min": 51, "max": 100, "dobava": 20, "prodaja": 28},
    {"min": 101, "max": 150, "dobava": 25, "prodaja": 35},
    {"min": 151, "max": 200, "dobava": 30, "prodaja": 42},
    {"min": 201, "max": 300, "dobava": 35, "prodaja": 49},
    {"min": 301, "max": 500, "dobava": 40, "prodaja": 56},
    {"min": 501, "max": 1000, "dobava": 65, "prodaja": 91}
]

cenik_letaki = [
    {"min": 1, "max": 50, "dobava": 25, "prodaja": 35},
    {"min": 51, "max": 100, "dobava": 30, "prodaja": 42},
    {"min": 101, "max": 200, "dobava": 45, "prodaja": 63},
    {"min": 201, "max": 300, "dobava": 55, "prodaja": 77},
    {"min": 301, "max": 500, "dobava": 65, "prodaja": 91},
    {"min": 501, "max": 1000, "dobava": 90, "prodaja": 126},
    {"min": 1001, "max": 2000, "dobava": 160, "prodaja": 224}
]

# T-shirt price lists
cenik_majice = [
    {"ime": "backfire", "min": 1, "max": 100, "dobava": 5.22, "prodaja": 6.26},
    {"ime": "beverly", "min": 1, "max": 100, "dobava": 5.95, "prodaja": 7.14},
    {"ime": "corporate", "min": 1, "max": 100, "dobava": 7.94, "prodaja": 9.53},
    {"ime": "fencer", "min": 1, "max": 100, "dobava": 5.22, "prodaja": 6.26},
    {"ime": "flag", "min": 1, "max": 100, "dobava": 5.40, "prodaja": 6.48},
    {"ime": "flextop", "min": 1, "max": 100, "dobava": 5.22, "prodaja": 6.26},
    {"ime": "florida", "min": 1, "max": 100, "dobava": 6.04, "prodaja": 7.25},
    {"ime": "florida fluo", "min": 1, "max": 100, "dobava": 8.24, "prodaja": 9.89},
    {"ime": "free", "min": 1, "max": 100, "dobava": 4.67, "prodaja": 5.60},
    {"ime": "free lady", "min": 1, "max": 100, "dobava": 4.67, "prodaja": 5.60},
    {"ime": "free lady melange", "min": 1, "max": 100, "dobava": 4.67, "prodaja": 5.60},
    {"ime": "free melange", "min": 1, "max": 100, "dobava": 4.67, "prodaja": 5.60},
    {"ime": "look", "min": 1, "max": 100, "dobava": 4.58, "prodaja": 5.50},
    {"ime": "look man", "min": 1, "max": 100, "dobava": 5.31, "prodaja": 6.37},
    {"ime": "party", "min": 1, "max": 100, "dobava": 5.22, "prodaja": 6.26},
    {"ime": "party lady", "min": 1, "max": 100, "dobava": 5.22, "prodaja": 6.26},
    {"ime": "pineta", "min": 1, "max": 100, "dobava": 8.11, "prodaja": 9.73},
    {"ime": "pineta lady", "min": 1, "max": 100, "dobava": 8.11, "prodaja": 9.73},
    {"ime": "pineta melange", "min": 1, "max": 100, "dobava": 8.11, "prodaja": 9.73},
    {"ime": "print (white)", "min": 1, "max": 100, "dobava": 3.57, "prodaja": 4.28},
    {"ime": "print (others)", "min": 1, "max": 100, "dobava": 3.97, "prodaja": 4.76},
    {"ime": "print melange", "min": 1, "max": 100, "dobava": 3.97, "prodaja": 4.76},
    {"ime": "print lady (white)", "min": 1, "max": 100, "dobava": 3.29, "prodaja": 3.95},
    {"ime": "print lady (others)", "min": 1, "max": 100, "dobava": 3.57, "prodaja": 4.28},
    {"ime": "runner", "min": 1, "max": 100, "dobava": 4.12, "prodaja": 4.94},
    {"ime": "runner lady", "min": 1, "max": 100, "dobava": 3.76, "prodaja": 4.51},
    {"ime": "running", "min": 1, "max": 100, "dobava": 8.24, "prodaja": 9.89},
    {"ime": "running lady", "min": 1, "max": 100, "dobava": 8.24, "prodaja": 9.89},
    {"ime": "shore", "min": 1, "max": 100, "dobava": 4.65, "prodaja": 5.58},
    {"ime": "smash", "min": 1, "max": 100, "dobava": 6.87, "prodaja": 8.24},
    {"ime": "sound+", "min": 1, "max": 100, "dobava": 5.22, "prodaja": 6.26},
    {"ime": "sound+ lady", "min": 1, "max": 100, "dobava": 5.22, "prodaja": 6.26},
    {"ime": "sunrise", "min": 1, "max": 100, "dobava": 5.51, "prodaja": 6.61},
    {"ime": "sunrise lady", "min": 1, "max": 100, "dobava": 5.51, "prodaja": 6.61},
    {"ime": "sunrise lady melange", "min": 1, "max": 100, "dobava": 5.51, "prodaja": 6.61},
    {"ime": "sunrise melange", "min": 1, "max": 100, "dobava": 5.51, "prodaja": 6.61},
    {"ime": "sunset (others)", "min": 1, "max": 100, "dobava": 4.41, "prodaja": 5.29},
    {"ime": "sunset (camouflage)", "min": 1, "max": 100, "dobava": 6.13, "prodaja": 7.36},
    {"ime": "sunset fluo", "min": 1, "max": 100, "dobava": 6.13, "prodaja": 7.36},
    {"ime": "sunset lady (others)", "min": 1, "max": 100, "dobava": 4.41, "prodaja": 5.29},
    {"ime": "sunset lady (camouflage)", "min": 1, "max": 100, "dobava": 6.13, "prodaja": 7.36},
    {"ime": "sunset lady melange", "min": 1, "max": 100, "dobava": 4.41, "prodaja": 5.29},
    {"ime": "sunset melange", "min": 1, "max": 100, "dobava": 4.41, "prodaja": 5.29},
    {"ime": "v-neck", "min": 1, "max": 100, "dobava": 4.67, "prodaja": 5.60},
    {"ime": "v-neck lady", "min": 1, "max": 100, "dobava": 4.67, "prodaja": 5.60},
    {"ime": "v-neck lady melange", "min": 1, "max": 100, "dobava": 4.67, "prodaja": 5.60},
    {"ime": "v-neck melange", "min": 1, "max": 100, "dobava": 4.67, "prodaja": 5.60},
    {"ime": "young", "min": 1, "max": 100, "dobava": 5.22, "prodaja": 6.26},
    {"ime": "young lady", "min": 1, "max": 100, "dobava": 5.22, "prodaja": 6.26},
    {"ime": "amalfi", "min": 1, "max": 100, "dobava": 8.60, "prodaja": 10.32},
    {"ime": "amalfi melange", "min": 1, "max": 100, "dobava": 8.60, "prodaja": 10.32},
    {"ime": "aviazione", "min": 1, "max": 100, "dobava": 14.30, "prodaja": 17.16},
    {"ime": "aviazione melange", "min": 1, "max": 100, "dobava": 14.30, "prodaja": 17.16},
    {"ime": "cambridge", "min": 1, "max": 100, "dobava": 12.81, "prodaja": 15.37},
    {"ime": "cambridge melange", "min": 1, "max": 100, "dobava": 12.81, "prodaja": 15.37},
    {"ime": "company", "min": 1, "max": 100, "dobava": 14.46, "prodaja": 17.35},
    {"ime": "chic", "min": 1, "max": 100, "dobava": 13.72, "prodaja": 16.46},
    {"ime": "florence", "min": 1, "max": 100, "dobava": 14.19, "prodaja": 17.03},
    {"ime": "florence lady", "min": 1, "max": 100, "dobava": 14.19, "prodaja": 17.03},
    {"ime": "florence lady melange", "min": 1, "max": 100, "dobava": 14.19, "prodaja": 17.03},
    {"ime": "florence melange", "min": 1, "max": 100, "dobava": 14.19, "prodaja": 17.03},
    {"ime": "france", "min": 1, "max": 100, "dobava": 12.72, "prodaja": 15.26},
    {"ime": "glamour", "min": 1, "max": 100, "dobava": 12.36, "prodaja": 14.83},
    {"ime": "italia", "min": 1, "max": 100, "dobava": 12.72, "prodaja": 15.26},
    {"ime": "italia melange", "min": 1, "max": 100, "dobava": 12.72, "prodaja": 15.26},
    {"ime": "leeds", "min": 1, "max": 100, "dobava": 12.81, "prodaja": 15.37},
    {"ime": "leeds melange", "min": 1, "max": 100, "dobava": 12.81, "prodaja": 15.37},
    {"ime": "long nation", "min": 1, "max": 100, "dobava": 16.02, "prodaja": 19.22},
    {"ime": "long nation lady", "min": 1, "max": 100, "dobava": 16.02, "prodaja": 19.22},
    {"ime": "long nation lady melange", "min": 1, "max": 100, "dobava": 16.02, "prodaja": 19.22},
    {"ime": "long nation melange", "min": 1, "max": 100, "dobava": 16.02, "prodaja": 19.22},
    {"ime": "memphis", "min": 1, "max": 100, "dobava": 11.90, "prodaja": 14.28},
    {"ime": "memphis lady", "min": 1, "max": 100, "dobava": 11.90, "prodaja": 14.28},
    {"ime": "nation", "min": 1, "max": 100, "dobava": 13.72, "prodaja": 16.46},
    {"ime": "nation lady", "min": 1, "max": 100, "dobava": 13.72, "prodaja": 16.46},
    {"ime": "nation lady melange", "min": 1, "max": 100, "dobava": 13.72, "prodaja": 16.46},
    {"ime": "nation melange", "min": 1, "max": 100, "dobava": 13.72, "prodaja": 16.46},
    {"ime": "nautic", "min": 1, "max": 100, "dobava": 12.36, "prodaja": 14.83},
    {"ime": "nautic lady", "min": 1, "max": 100, "dobava": 12.36, "prodaja": 14.83},
    {"ime": "prestige", "min": 1, "max": 100, "dobava": 12.36, "prodaja": 14.83},
    {"ime": "prestige melange", "min": 1, "max": 100, "dobava": 12.36, "prodaja": 14.83},
    {"ime": "rome", "min": 1, "max": 100, "dobava": 8.60, "prodaja": 10.32},
    {"ime": "rome lady", "min": 1, "max": 100, "dobava": 8.60, "prodaja": 10.32},
    {"ime": "rome lady melange", "min": 1, "max": 100, "dobava": 8.60, "prodaja": 10.32},
    {"ime": "rome melange", "min": 1, "max": 100, "dobava": 8.60, "prodaja": 10.32},
    {"ime": "skipper", "min": 1, "max": 100, "dobava": 12.72, "prodaja": 15.26},
    {"ime": "skipper lady", "min": 1, "max": 100, "dobava": 12.72, "prodaja": 15.26},
    {"ime": "skipper lady melange", "min": 1, "max": 100, "dobava": 12.72, "prodaja": 15.26},
    {"ime": "spain", "min": 1, "max": 100, "dobava": 12.72, "prodaja": 15.26},
    {"ime": "training", "min": 1, "max": 100, "dobava": 11.90, "prodaja": 14.28},
    {"ime": "training lady", "min": 1, "max": 100, "dobava": 11.90, "prodaja": 14.28},
    {"ime": "venice", "min": 1, "max": 100, "dobava": 10.61, "prodaja": 12.73},
    {"ime": "venice lady", "min": 1, "max": 100, "dobava": 10.61, "prodaja": 12.73},
    {"ime": "venice lady melange", "min": 1, "max": 100, "dobava": 10.61, "prodaja": 12.73},
    {"ime": "venice melange", "min": 1, "max": 100, "dobava": 10.61, "prodaja": 12.73},
    {"ime": "venice pro", "min": 1, "max": 100, "dobava": 10.61, "prodaja": 12.73},
    {"ime": "verona", "min": 1, "max": 100, "dobava": 12.72, "prodaja": 15.26},
    {"ime": "alabama", "min": 1, "max": 100, "dobava": 21.04, "prodaja": 25.25},
    {"ime": "alabama melange", "min": 1, "max": 100, "dobava": 21.04, "prodaja": 25.25},
    {"ime": "atlanta+", "min": 1, "max": 100, "dobava": 26.54, "prodaja": 31.85},
    {"ime": "atlanta+ fluo", "min": 1, "max": 100, "dobava": 26.54, "prodaja": 31.85},
    {"ime": "atlanta+ lady", "min": 1, "max": 100, "dobava": 26.54, "prodaja": 31.85},
    {"ime": "atlanta+ lady fluo", "min": 1, "max": 100, "dobava": 26.54, "prodaja": 31.85},
    {"ime": "atlanta+ lady melange", "min": 1, "max": 100, "dobava": 26.54, "prodaja": 31.85},
    {"ime": "atlanta+ melange", "min": 1, "max": 100, "dobava": 26.54, "prodaja": 31.85},
    {"ime": "austin", "min": 1, "max": 100, "dobava": 21.56, "prodaja": 25.87},
    {"ime": "boxer+", "min": 1, "max": 100, "dobava": 17.38, "prodaja": 20.86},
    {"ime": "boxer+ lady", "min": 1, "max": 100, "dobava": 17.38, "prodaja": 20.86},
    {"ime": "canada", "min": 1, "max": 100, "dobava": 17.02, "prodaja": 20.42},
    {"ime": "canada melange", "min": 1, "max": 100, "dobava": 17.02, "prodaja": 20.42},
    {"ime": "carson", "min": 1, "max": 100, "dobava": 15.19, "prodaja": 18.23},
    {"ime": "class+", "min": 1, "max": 100, "dobava": 31.48, "prodaja": 37.78},
    {"ime": "class+ lady", "min": 1, "max": 100, "dobava": 31.48, "prodaja": 37.78},
    {"ime": "dallas+", "min": 1, "max": 100, "dobava": 28.36, "prodaja": 34.03},
    {"ime": "dallas+ fluo", "min": 1, "max": 100, "dobava": 28.36, "prodaja": 34.03},
    {"ime": "dallas+ lady", "min": 1, "max": 100, "dobava": 28.36, "prodaja": 34.03},
    {"ime": "dallas+ lady melange", "min": 1, "max": 100, "dobava": 28.36, "prodaja": 34.03},
    {"ime": "dallas+ melange", "min": 1, "max": 100, "dobava": 28.36, "prodaja": 34.03},
    {"ime": "derby", "min": 1, "max": 100, "dobava": 32.30, "prodaja": 38.76},
    {"ime": "derby lady", "min": 1, "max": 100, "dobava": 32.30, "prodaja": 38.76},
    {"ime": "hawaii+", "min": 1, "max": 100, "dobava": 22.88, "prodaja": 27.46},
    {"ime": "hawaii+ lady", "min": 1, "max": 100, "dobava": 22.88, "prodaja": 27.46},
    {"ime": "hoover", "min": 1, "max": 100, "dobava": 18.12, "prodaja": 21.74},
    {"ime": "houston", "min": 1, "max": 100, "dobava": 17.53, "prodaja": 21.04},
    {"ime": "houston melange", "min": 1, "max": 100, "dobava": 17.53, "prodaja": 21.04},
    {"ime": "kansas", "min": 1, "max": 100, "dobava": 32.30, "prodaja": 38.76},
    {"ime": "malibu+", "min": 1, "max": 100, "dobava": 19.60, "prodaja": 23.52},
    {"ime": "malibu+ lady", "min": 1, "max": 100, "dobava": 19.60, "prodaja": 23.52},
    {"ime": "malibu+ lady melange", "min": 1, "max": 100, "dobava": 19.60, "prodaja": 23.52},
    {"ime": "malibu+ melange", "min": 1, "max": 100, "dobava": 19.60, "prodaja": 23.52},
    {"ime": "maverick 2.0", "min": 1, "max": 100, "dobava": 27.45, "prodaja": 32.94},
    {"ime": "melbourne", "min": 1, "max": 100, "dobava": 28.36, "prodaja": 34.03},
    {"ime": "melbourne fluo", "min": 1, "max": 100, "dobava": 28.36, "prodaja": 34.03},
    {"ime": "melbourne melange", "min": 1, "max": 100, "dobava": 28.36, "prodaja": 34.03},
    {"ime": "miami+", "min": 1, "max": 100, "dobava": 20.68, "prodaja": 24.82},
    {"ime": "miami+ fluo", "min": 1, "max": 100, "dobava": 20.68, "prodaja": 24.82},
    {"ime": "miami+ lady", "min": 1, "max": 100, "dobava": 20.68, "prodaja": 24.82},
    {"ime": "miami+ lady melange", "min": 1, "max": 100, "dobava": 20.68, "prodaja": 24.82},
    {"ime": "miami+ melange", "min": 1, "max": 100, "dobava": 20.68, "prodaja": 24.82},
    {"ime": "miami+ summer", "min": 1, "max": 100, "dobava": 17.93, "prodaja": 21.52},
    {"ime": "mistral+", "min": 1, "max": 100, "dobava": 17.02, "prodaja": 20.42},
    {"ime": "mistral+ fluo", "min": 1, "max": 100, "dobava": 17.02, "prodaja": 20.42},
    {"ime": "mistral+ lady", "min": 1, "max": 100, "dobava": 17.02, "prodaja": 20.42},
    {"ime": "mistral+ lady melange", "min": 1, "max": 100, "dobava": 17.02, "prodaja": 20.42},
    {"ime": "mistral+ melange", "min": 1, "max": 100, "dobava": 17.02, "prodaja": 20.42},
    {"ime": "mistral+ summer", "min": 1, "max": 100, "dobava": 15.92, "prodaja": 19.10},
    {"ime": "nazionale", "min": 1, "max": 100, "dobava": 28.36, "prodaja": 34.03},
    {"ime": "nazionale lady", "min": 1, "max": 100, "dobava": 28.36, "prodaja": 34.03},
    {"ime": "nevada", "min": 1, "max": 100, "dobava": 32.30, "prodaja": 38.76},
    {"ime": "new orleans", "min": 1, "max": 100, "dobava": 12.03, "prodaja": 14.44},
    {"ime": "new orleans melange", "min": 1, "max": 100, "dobava": 12.03, "prodaja": 14.44},
    {"ime": "orlando", "min": 1, "max": 100, "dobava": 14.84, "prodaja": 17.81},
    {"ime": "orlando melange", "min": 1, "max": 100, "dobava": 14.84, "prodaja": 17.81},
    {"ime": "panama+", "min": 1, "max": 100, "dobava": 25.99, "prodaja": 31.19},
    {"ime": "panama+ fluo", "min": 1, "max": 100, "dobava": 25.99, "prodaja": 31.19},
    {"ime": "panama+ lady", "min": 1, "max": 100, "dobava": 25.99, "prodaja": 31.19},
    {"ime": "panama+ lady melange", "min": 1, "max": 100, "dobava": 25.99, "prodaja": 31.19},
    {"ime": "panama+ melange", "min": 1, "max": 100, "dobava": 25.99, "prodaja": 31.19},
    {"ime": "panama+ summer", "min": 1, "max": 100, "dobava": 21.23, "prodaja": 25.48},
    {"ime": "pontiac", "min": 1, "max": 100, "dobava": 19.40, "prodaja": 23.28},
    {"ime": "portland", "min": 1, "max": 100, "dobava": 21.23, "prodaja": 25.48},
    {"ime": "portland melange", "min": 1, "max": 100, "dobava": 21.23, "prodaja": 25.48},
    {"ime": "rio", "min": 1, "max": 100, "dobava": 24.70, "prodaja": 29.64},
    {"ime": "sydney", "min": 1, "max": 100, "dobava": 28.36, "prodaja": 34.03},
    {"ime": "sydney fluo", "min": 1, "max": 100, "dobava": 28.36, "prodaja": 34.03},
    {"ime": "sydney melange", "min": 1, "max": 100, "dobava": 28.36, "prodaja": 34.03},
    {"ime": "toledo", "min": 1, "max": 100, "dobava": 17.57, "prodaja": 21.08},
    {"ime": "toronto", "min": 1, "max": 100, "dobava": 19.40, "prodaja": 23.28},
    {"ime": "toronto melange", "min": 1, "max": 100, "dobava": 19.40, "prodaja": 23.28},
    {"ime": "vancouver", "min": 1, "max": 100, "dobava": 29.38, "prodaja": 35.26},
    {"ime": "vancouver melange", "min": 1, "max": 100, "dobava": 29.38, "prodaja": 35.26},
    {"ime": "work 2.0", "min": 1, "max": 100, "dobava": 41.18, "prodaja": 49.42},
    {"ime": "fruit of the loom", "min": 1, "max": 100, "dobava": 2.70, "prodaja": 3.70},
    {"ime": "imperial sols", "min": 1, "max": 100, "dobava": 3.14, "prodaja": 4.90}
]

promocijski_material = {
    "gravura": cenik_gravura,
    "dotisk na bloke": cenik_bloki,
    "vzigalniki": cenik_vzigalniki,
    "vizitke": cenik_vizitke,
    "letaki": cenik_letaki
}

cenik_dtf = {
    1: (27, 38),
    2: (40, 56),
    4: (72, 101),
    5: (90, 126),
    6: (110, 154),
    7: (126, 177),
    8: (144, 202),
    9: (162, 227),
    10: (180, 252),
    11: (200, 280),
    12: (215, 301),
}

def sanitize_filename(name):
    """Sanitize a string to be safe for use as a filename."""
    return re.sub(r'[<>:"/\\|?*]', '_', name.strip())

def poisci_razpon(cenik, kolicina, ime_izdelka=None):
    """Find the appropriate price range for a given quantity and optionally item name."""
    if ime_izdelka:
        for razpon in cenik:
            if razpon["min"] <= kolicina <= razpon["max"] and razpon["ime"] == ime_izdelka:
                return razpon
    else:
        for razpon in cenik:
            if razpon["min"] <= kolicina <= razpon["max"]:
                return razpon
    return None

def interpoliraj_ceno(metri, cenik):
    """Interpolate the cost based on the length in meters, including <1m."""
    tocke = sorted(cenik.keys())
    
    if metri <= 0:
        return 0, 0
    
    if metri < tocke[0]:
        d1, p1 = 0, 0
        d2, p2 = cenik[tocke[0]]
        faktor = metri / tocke[0]
        dobavna = d1 + (d2 - d1) * faktor
        prodajna = p1 + (p2 - p1) * faktor
        return round(dobavna, 2), round(prodajna, 2)
    
    for i in range(len(tocke) - 1):
        nizji = tocke[i]
        visji = tocke[i + 1]
        if nizji <= metri <= visji:
            d1, p1 = cenik[nizji]
            d2, p2 = cenik[visji]
            faktor = (metri - nizji) / (visji - nizji)
            dobavna = d1 + (d2 - d1) * faktor
            prodajna = p1 + (p2 - p1) * faktor
            return round(dobavna, 2), round(prodajna, 2)
    
    return cenik[tocke[-1]]

def save_to_file(podjetje, data, kolicina_or_metri, izbira, mapa="izracuni_dtf"):
    """Save calculation results to a text file."""
    os.makedirs(mapa, exist_ok=True)
    sanitized_podjetje = sanitize_filename(podjetje)
    sanitized_izbira = sanitize_filename(izbira)
    unit = "m" if izbira == "dtf" else "kos"
    ime_datoteke = f"{sanitized_podjetje}_{sanitized_izbira}_{kolicina_or_metri}{unit}.txt"
    pot = os.path.join(mapa, ime_datoteke)
    try:
        with open(pot, "w", encoding="utf-8") as f:
            f.write(f"Podjetje: {podjetje}\n")
            for line in data:
                f.write(f"{line}\n")
        print(f"\n✅ Shranjeno v: {pot}")
    except OSError as e:
        print(f"❌ Napaka pri shranjevanju datoteke: {e}")

def create_pdf_layout(podjetje, artikel_ime, logotipi, mapa="izracuni_dtf"):
    """Create a PDF showing the layout of logos on a 44cm x 100cm sheet."""
    os.makedirs(mapa, exist_ok=True)
    sanitized_podjetje = sanitize_filename(podjetje)
    sanitized_izbira = sanitize_filename(artikel_ime if artikel_ime != "ne potrebujem ga" else "dtf")
    pdf_path = os.path.join(mapa, f"{sanitized_podjetje}_{sanitized_izbira}_layout.pdf")
    
    PAGE_WIDTH = 44 * cm
    PAGE_HEIGHT = 100 * cm
    c = canvas.Canvas(pdf_path, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    
    y_position = PAGE_HEIGHT - 1 * cm
    
    for logo in logotipi:
        file_path, sirina, visina, kolicina, rotirano, log_na_vrstico, vrstic = logo
        logo_width = visina * cm if rotirano else sirina * cm
        logo_height = sirina * cm if rotirano else visina * cm
        
        # Preveri format datoteke
        if file_path.lower().endswith('.pdf'):
            try:
                pdf_reader = PdfReader(file_path)
                if len(pdf_reader.pages) == 0:
                    raise ValueError("PDF datoteka je prazna.")
                page = pdf_reader.pages[0]  # Prva stran PDF-ja
                # Pretvori PDF stran v sliko, saj neposredno risanje ni podprto
                from reportlab.pdfgen import pdfimage
                img = pdfimage.PDFImage(file_path, 0)  # 0 je indeks prve strani
            except Exception as e:
                print(f"⚠️ Napaka pri obdelavi PDF datoteke {file_path}: {e}")
                c.drawString(0, y_position - logo_height, f"[Napaka: PDF {os.path.basename(file_path)} ni naložen]")
                continue
        elif file_path.lower().endswith('.svg'):
            try:
                drawing = svg2rlg(file_path)
                if not drawing:
                    raise ValueError("SVG datoteka ni pravilno formatirana.")
            except Exception as e:
                print(f"⚠️ Napaka pri vstavljanju SVG {file_path}: {e}")
                c.drawString(0, y_position - logo_height, f"[Napaka: SVG {os.path.basename(file_path)} ni naložen]")
                continue
        else:  # PNG/JPG
            try:
                img = Image.open(file_path)
            except Exception as e:
                print(f"⚠️ Napaka pri vstavljanju slike {file_path}: {e}")
                c.drawString(0, y_position - logo_height, f"[Napaka: Slika {os.path.basename(file_path)} ni naložena]")
                continue

        for vrstica in range(vrstic):
            for i in range(log_na_vrstico):
                if kolicina <= 0:
                    break
                x_position = i * logo_width
                if x_position + logo_width > PAGE_WIDTH or y_position - logo_height < 0:
                    break
                
                try:
                    if file_path.lower().endswith('.pdf'):
                        # Uporabi PDFImage za risanje
                        c.drawImage(img, x_position, y_position - logo_height, width=logo_width, height=logo_height)
                    elif file_path.lower().endswith('.svg'):
                        if rotirano:
                            c.saveState()
                            c.translate(x_position + logo_width, y_position)
                            c.rotate(-90)
                            renderPDF.draw(drawing, c, 0, -logo_height, scale=logo_width/drawing.width)
                            c.restoreState()
                        else:
                            renderPDF.draw(drawing, c, x_position, y_position - logo_height, width=logo_width, height=logo_height)
                    else:
                        if rotirano:
                            img_rot = img.rotate(90, expand=True)
                            c.drawImage(file_path, x_position, y_position - logo_height, width=logo_width, height=logo_height)
                        else:
                            c.drawImage(file_path, x_position, y_position - logo_height, width=logo_width, height=logo_height)
                except Exception as e:
                    print(f"⚠️ Napaka pri risanju logotipa {file_path}: {e}")
                    c.drawString(x_position, y_position - logo_height, f"[Napaka: Logotip {os.path.basename(file_path)} ni naložen]")
                
                kolicina -= 1
            y_position -= logo_height
            if y_position < logo_height:
                c.showPage()
                y_position = PAGE_HEIGHT - 1 * cm
    
    c.save()
    print(f"\n✅ PDF razporeditev shranjena v: {pdf_path}")

def izracun_promocije():
    """Calculate costs for promotional materials."""
    try:
        podjetje = input("Vpiši ime podjetja: ").strip()
        if not podjetje:
            print("❌ Ime podjetja ne sme biti prazno.")
            return

        print("\nIzberi promocijski izdelek (gravura, dotisk na bloke, vzigalniki, vizitke, letaki):")
        izbira = input("Vpiši ime izdelka: ").lower().strip()
        if izbira not in promocijski_material:
            print("❌ Napačen izdelek. Izberi iz seznama (gravura, dotisk na bloke, vzigalniki, vizitke, letaki).")
            return

        kolicina = input("Vpiši količino: ").strip()
        try:
            kolicina = int(kolicina)
            if kolicina <= 0:
                raise ValueError("Količina mora biti pozitivna.")
        except ValueError:
            print("❌ Napačen vnos količine. Vnesi celo število.")
            return

        cenik = promocijski_material[izbira]
        razpon = poisci_razpon(cenik, kolicina)
        if razpon is None:
            print("❌ Napačna količina za izbrani izdelek.")
            return

        dobava = razpon["dobava"]
        prodaja = razpon["prodaja"]
        profit = round(prodaja - dobava, 2)
        cena_na_kos = round(prodaja / kolicina, 3) if kolicina else 0

        print("\n=== REZULTAT ===")
        print(f"Podjetje: {podjetje}")
        print(f"Artikel: {izbira.title()} | Količina: {kolicina}")
        print(f"Dobavna cena: {dobava} €")
        print(f"Prodajna cena: {prodaja} €")
        print(f"Profit: {profit} €")
        print(f"Cena na kos: {cena_na_kos} €")

        data = [
            f"Artikel: {izbira.title()}",
            f"Količina: {kolicina}",
            f"Dobavna cena: {dobava} €",
            f"Prodajna cena: {prodaja} €",
            f"Profit: {profit} €",
            f"Cena na kos: {cena_na_kos} €"
        ]
        save_to_file(podjetje, data, kolicina, izbira)

    except Exception as e:
        print(f"❌ Napaka: {e}")

def izracun_dtf():
    """Calculate costs for DTF printing with clothing articles and create PDF layout."""
    try:
        podjetje = input("Vpiši ime podjetja: ").strip()
        if not podjetje:
            print("❌ Ime podjetja ne sme biti prazno.")
            return

        izbira = input("Vpiši ime oblačilnega artikla (npr. backfire, ali 'ne potrebujem ga' za lastne izdelke): ").lower().strip()
        
        if izbira == "ne potrebujem ga":
            artikel_dobava = 0
            artikel_prodaja = 0
            artikel_ime = "ne potrebujem ga"
            cenik_izbira = None
        else:
            if izbira not in [razpon["ime"].lower() for razpon in cenik_majice]:
                print("❌ Napačen izdelek. Vnesi veljaven oblačilni artikel (npr. backfire) ali 'ne potrebujem ga'.")
                return
            cenik_izbira = cenik_majice
            artikel_ime = izbira

        try:
            skupna_kolicina = int(input("Vpiši skupno količino izdelkov: ").strip())
            if skupna_kolicina <= 0:
                raise ValueError("Količina mora biti pozitivna.")
        except ValueError:
            print("❌ Napačen vnos količine. Vnesi celo število.")
            return

        if cenik_izbira:
            razpon = poisci_razpon(cenik_izbira, skupna_kolicina, artikel_ime)
            if razpon is None:
                print("❌ Napačna količina ali izdelek.")
                return
            artikel_dobava = razpon["dobava"] * skupna_kolicina
            artikel_prodaja = razpon["prodaja"] * skupna_kolicina
        else:
            artikel_dobava = 0
            artikel_prodaja = 0

        st_logotipov = input("Koliko različnih vrst logotipov boš vnesel? ").strip()
        try:
            st_logotipov = int(st_logotipov)
            if st_logotipov <= 0:
                raise ValueError("Število logotipov mora biti pozitivno.")
        except ValueError:
            print("❌ Napačen vnos števila logotipov. Vnesi celo število.")
            return

        skupna_povrsina_cm2 = 0
        podrobnosti = []
        logotipi = []

        for i in range(1, st_logotipov + 1):
            print(f"\nVnos za logotip #{i}:")
            try:
                file_path = input("  Pot do datoteke logotipa (PDF, PNG, JPG, SVG): ").strip()
                if not os.path.isfile(file_path) or not file_path.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg', '.svg')):
                    raise ValueError("Neveljavna datoteka ali format (potrebno PDF, PNG, JPG ali SVG).")
                
                sirina = float(input("  Širina logotipa (v cm): "))
                visina = float(input("  Višina logotipa (v cm): "))
                kolicina = int(input("  Količina tega logotipa: "))
                if sirina <= 0 or visina <= 0 or kolicina <= 0:
                    raise ValueError("Vrednosti morajo biti pozitivne.")
            except ValueError as e:
                print(f"❌ Napačen vnos: {e}")
                return

            log_na_vrstico = math.floor(44 / sirina) if sirina > 0 else 0
            vrstic = math.ceil(kolicina / log_na_vrstico) if log_na_vrstico > 0 else 1
            visina_total = vrstic * visina

            rot_log_na_vrstico = math.floor(44 / visina) if visina > 0 else 0
            rot_vrstic = math.ceil(kolicina / rot_log_na_vrstico) if rot_log_na_vrstico > 0 else 1
            rot_visina_total = rot_vrstic * sirina

            rotirano = rot_visina_total < visina_total and rot_log_na_vrstico > 0
            if rotirano:
                vrstica_opis = (
                    f"Logotip #{i}: {kolicina} × {visina}x{sirina} cm (ROTIRANO) → "
                    f"{rot_log_na_vrstico} na vrstico, {rot_vrstic} vrstic = {rot_visina_total:.2f} cm"
                )
            else:
                vrstica_opis = (
                    f"Logotip #{i}: {kolicina} × {sirina}x{visina} cm → "
                    f"{log_na_vrstico} na vrstico, {vrstic} vrstic = {visina_total:.2f} cm"
                )

            podrobnosti.append(vrstica_opis)
            logotipi.append((file_path, sirina, visina, kolicina, rotirano, rot_log_na_vrstico if rotirano else log_na_vrstico, rot_vrstic if rotirano else vrstic))
            povrsina = sirina * visina * kolicina
            skupna_povrsina_cm2 += povrsina

        povrsinska_dolzina_m = skupna_povrsina_cm2 / (44 * 100)
        povrsinska_z_rezervo = round(povrsinska_dolzina_m + 0.2, 2)
        dtf_dobava, dtf_prodaja = interpoliraj_ceno(povrsinska_z_rezervo, cenik_dtf)

        skupna_dobava = round(dtf_dobava + artikel_dobava, 2)
        skupna_prodaja = round(dtf_prodaja + artikel_prodaja, 2)
        profit = round(skupna_prodaja - skupna_dobava, 2)
        cena_na_kos = round(skupna_prodaja / skupna_kolicina, 3) if skupna_kolicina else 0

        print("\n=== REZULTAT ===")
        print(f"Podjetje: {podjetje}")
        print(f"Artikel: {artikel_ime.title()}")
        print(f"Količina: {skupna_kolicina}")
        for vrstica in podrobnosti:
            print("  " + vrstica)
        print("\nDTF tisk:")
        print(f"  Referenčna dolžina: {povrsinska_z_rezervo} m")
        print(f"  Dobavna cena: {dtf_dobava} €")
        print(f"  Prodajna cena: {dtf_prodaja} €")
        if artikel_ime != "ne potrebujem ga":
            print(f"{artikel_ime.title()}:")
            print(f"  Dobavna cena: {artikel_dobava:.2f} €")
            print(f"  Prodajna cena: {artikel_prodaja:.2f} €")
        print("Skupaj:")
        print(f"  Dobavna cena: {skupna_dobava} €")
        print(f"  Prodajna cena: {skupna_prodaja} €")
        print(f"  Profit: {profit} €")
        print(f"  Cena na kos: {cena_na_kos} €")

        data = [
            f"Artikel: {artikel_ime.title()}",
            f"Količina: {skupna_kolicina}"
        ] + podrobnosti + [
            f"DTF tisk:",
            f"  Referenčna dolžina: {povrsinska_z_rezervo} m",
            f"  Dobavna cena: {dtf_dobava} €",
            f"  Prodajna cena: {dtf_prodaja} €"
        ]
        if artikel_ime != "ne potrebujem ga":
            data += [
                f"{artikel_ime.title()}:",
                f"  Dobavna cena: {artikel_dobava:.2f} €",
                f"  Prodajna cena: {artikel_prodaja:.2f} €"
            ]
        data += [
            f"Skupaj:",
            f"  Dobavna cena: {skupna_dobava} €",
            f"  Prodajna cena: {skupna_prodaja} €",
            f"  Profit: {profit} €",
            f"  Cena na kos: {cena_na_kos} €"
        ]
        save_to_file(podjetje, data, skupna_kolicina, artikel_ime if artikel_ime != "ne potrebujem ga" else "dtf")

        create_pdf_layout(podjetje, artikel_ime, logotipi)

    except Exception as e:
        print(f"❌ Napaka: {e}")

if __name__ == "__main__":
    while True:
        print("\nKaj želiš izračunati?")
        print("1. Promocijski material")
        print("2. DTF tisk (oblačila)")
        print("3. Izhod")
        izbira = input("Izberi [1/2/3]: ").strip()
        if izbira == "1":
            izracun_promocije()
        elif izbira == "2":
            izracun_dtf()
        elif izbira == "3":
            print("✅ Izhod.")
            break
        else:
            print("❌ Napačen vnos. Izberi 1, 2 ali 3.")
