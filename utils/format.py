import os
import json
import numpy
import re
import torch
import torch_rl

import utils

def get_vocab_path(run_dir):
    return os.path.join(run_dir, "vocab.json")

class Vocabulary:
    def __init__(self, run_dir):
        self.path = get_vocab_path(run_dir)
        self.max_size = 100
        self.vocab = {}
        if os.path.exists(self.path):
            self.vocab = json.load(open(self.path))

    def __getitem__(self, token):
        if not(token in self.vocab.keys()):
            if len(self.vocab) >= self.max_size:
                raise ValueError("Maximum vocabulary capacity reached")
            self.vocab[token] = len(self.vocab) + 1
        return self.vocab[token]

    def save(self):
        utils.create_folders_if_necessary(self.path)
        json.dump(self.vocab, open(self.path, "w"))

class ObssPreprocessor:
    def __init__(self, run_dir, obs_space):
        self.vocab = Vocabulary(run_dir)
        self.obs_space = {
            "image": 147,
            "instr": self.vocab.max_size
        }

    def __call__(self, obss, device=None):
        obs_ = torch_rl.DictList()

        if "image" in self.obs_space.keys():
            images = numpy.array([obs["image"] for obs in obss])
            images = torch.tensor(images, device=device, dtype=torch.float)

            obs_.image = images

        if "instr" in self.obs_space.keys():
            raw_instrs = []
            max_instr_len = 0

            for obs in obss:
                tokens = re.findall("([a-z]+)", obs["mission"].lower())
                instr = numpy.array([self.vocab[token] for token in tokens])
                raw_instrs.append(instr)
                max_instr_len = max(len(instr), max_instr_len)

            instrs = numpy.zeros((len(obss), max_instr_len))

            for i, instr in enumerate(raw_instrs):
                instrs[i, :len(instr)] = instr

            instrs = torch.tensor(instrs, device=device, dtype=torch.long)

            obs_.instr = instrs

        return obs_