#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  formula2image.py
#  Turns bunch of formulas into images and dataset listing
#
#  © Copyright 2016, Anssi "Miffyli" Kanervisto
#  
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#  

"""
Purpose of this script is to turn list of tex formulas into images
and a dataset list for OpenAI im2latex task.
Script outputs two lists:
    - im2latex.lst
        - Each row is: [idx of formula] [image name] [render type]
            - idx of formula is the line number in im2latex_formulas.lst
            - image name is name of the image (without filetype) 
            - render type is name of the method used to draw the picture
              (See RENDERING_SETUPS)
    - im2latex_formulas.lst
        - List of formulas, one per line
            -> No \n characters in formulas (doesn't affect math tex)
"""

import glob
import sys
import os
from multiprocessing import Pool
from subprocess import call

# Max number of formulas included
MAX_NUMBER = 150*1000

THREADS = 4

IMAGE_DIR = "formula_images"
DATASET_FILE = "im2latex.lst"
NEW_FORMULA_FILE = "im2latex_formulas.lst"

DEVNULL = open(os.devnull, "w")

BASIC_SKELETON = r"""
\documentclass[12pt]{article}
\pagestyle{empty}
\begin{document}

\begin{displaymath}
%s
\end{displaymath}

\end{document}
"""

# Different settings used to render images
# in format key: [skeleton, rendering_call]
#   - skeleton is the LaTeX code in which formula is inserted 
#     (see BASIC_SKELETON)
#   - rendering_call is the system call made to turn .tex into .png
# Each rendering setup is done for each formula.
# key/name is used to identify different renderings in dataset file

#RENDERING_SETUPS = {"basic": [BASIC_SKELETON, "./textogif -png -dpi 200 %s"]}
RENDERING_SETUPS = {"basic": [BASIC_SKELETON, 
                              "convert -density 200 -quality 100 %s.pdf %s.png"]
                   }

def remove_temp_files(name):
    """ Removes .aux, .log, .pdf and .tex files for name """
    os.remove(name+".aux")
    os.remove(name+".log")
    os.remove(name+".pdf")
    os.remove(name+".tex")

def formula_to_image(formula):
    """ Turns given formula into images based on RENDERING_SETUPS
    returns list of lists [[image_name, rendering_setup], ...], one list for
    each rendering.
    Return None if couldn't render the formula"""
    # Change to image dir because textogif doesn't seem to work otherwise...
    if not IMAGE_DIR in os.getcwd():
        os.chdir(IMAGE_DIR)
    formula = formula.strip("%")
    name = ("%x" % abs(hash(formula)))[:10] #Hopefully unique enough name
    ret = []
    for rend_name, rend_setup in RENDERING_SETUPS.items():
        # Create latex source
        latex = rend_setup[0] % formula
        full_path = name+"_"+rend_name
        # Write latex source
        with open(full_path+".tex", "w") as f:
            f.write(latex)
        
        # Call pdflatex to turn .tex into .pdf
        code = call(["pdflatex", '-interaction=nonstopmode', full_path+".tex"], 
                    stdout=DEVNULL, stderr=DEVNULL)
        if code != 0:
            os.system("rm -rf "+full_path+"*")
            return None
        
        # Turn .pdf to .png
        # Handles variable number of places to insert path.
        # i.e. "%s.tex" vs "%s.pdf %s.png"
        full_path_strings = rend_setup[1].count("%")*(full_path,)
        code = call((rend_setup[1] % full_path_strings).split(" "),
                    stdout=DEVNULL, stderr=DEVNULL)
        
        #Remove files
        try:
            remove_temp_files(full_path)
        except Exception as e:
            # try-except in case one of the previous scripts removes these files
            # already
            return None
        
        if code != 0:
            # Error during rendering, remove files and return None
            os.system("rm -rf "+full_path+"*")
            return None
        else: 
            ret.append([full_path, rend_name])
    return ret
    
            
def main(formula_list):
    formulas = open(formula_list).read().split("\n")[:MAX_NUMBER]
    try:
        os.mkdir(IMAGE_DIR)
    except OSError as e:
        pass #except because throws OSError if dir exists
    print("Turning formulas into images...")
    
    # Running a thread pool masks debug output. Uncomment command below to run
    # formulas over images sequentially to see debug errors more clearly
    
    # names = [formula_to_image(formula) for formula in formulas]
    
    # Also remember to comment threaded version if you use sequential:
    pool = Pool(THREADS)
    names = list(pool.imap(formula_to_image, formulas))
    
    zipped = list(zip(formulas, names))
    
    new_dataset_lines = []
    new_formulas = []
    ctr = 0
    for formula in zipped:
        if formula[1] is None:
            continue
        for rendering_setup in formula[1]:
            new_dataset_lines.append(str(ctr)+" "+" ".join(rendering_setup))
        new_formulas.append(formula[0])
        ctr += 1
    
    with open(NEW_FORMULA_FILE, "w") as f:
        f.write("\n".join(new_formulas))
    
    with open(DATASET_FILE, "w") as f:
        f.write("\n".join(new_dataset_lines))

def check_validity(dataset_file, formula_file, formula_dir):
    """ Checks if lists are valid, ie. no files missing etc """
    dataset_lines = open(dataset_file).read().split("\n")
    formula_file = open(formula_file).read().split("\n")
    formula_images = os.listdir(formula_dir)
    max_id = 0
    missing_files = 0
    
    for line in dataset_lines:
        if line == "": continue
        splt = line.split(" ")
        max_id = splt[0]
        if not splt[1]+".png" in formula_images:
            missing_files += 1
    
    if int(max_id) != len(formula_file): 
        print("Max id in dataset != formula_file length (%d vs %d)" % 
              (int(max_id), len(formula_file)))
    
    print("%d files missing" % missing_files)
    
if __name__ == '__main__':
    if len(sys.argv) != 2 and len(sys.argv) != 4:
        print("To generate datasets:           formula2image.py formulalist\n"+
              "To validate generated datasets: "+
                "formula2image.py dataset_list formula_list formula_dir")
    elif len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        check_validity(sys.argv[1], sys.argv[2], sys.argv[3]) 

