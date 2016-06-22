#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  im2latex_utils.py
#  Collection of tools to help with im2latex  
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
import re
import random 

TOKENIZE_PATTERN = re.compile("(\\[a-zA-Z]+)|(\w)")
LABEL_PATTERN = re.compile("(\\label{.*?})")


def tokenize_formula(formula):
    """ [WIP] Returns list of tokens in given formula.
    Note: \label(...) and whitespaces will be removed
    Note2: WIP and needs confirming this is correct way"""
    #Remove \label
    tokens = re.sub(LABEL_PATTERN, "", tokens)
    #Tokenize
    tokens = re.split(TOKENIZE_PATTERN, tokens)
    #Clean up
    tokens = [x for x in tokens if x is not None and x != ""]
    return tokens

def split_train_validate_test(array, frac=0.8):
    """ Splits given array into train, validation and test sets
    First splits array into train-test sets (frac for train, 1-frac for test),
    then splits train set into train-validation (again, frac for train and
    1-frac for validation)
    array - array to be splitted into three non-overlapping sets
    frac  - Fraction of items to keep in train set in splits
    Returns list of lists [train, validation, test]"""
    idxs = set(range(len(array))) 
    #Take test set
    test_idxs = set(random.sample(idxs, int(len(idxs)*(1.0-frac))))
    idxs = idxs-test_idxs
    
    validate_idxs = set(random.sample(idxs, int(len(idxs)*(1.0-frac))))
    idxs = idxs-validate_idxs
    
    test = [array[i] for i in test_idxs]
    validate = [array[i] for i in validate_idxs]
    train = [array[i] for i in idxs]
    return [train, validate, test]
