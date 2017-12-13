"""
Copyright 2017 Neural Networks and Deep Learning lab, MIPT

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import logging
import random
import itertools
from overrides import overrides
from typing import Dict, Tuple, List, Generator, Any

from deeppavlov.core.common.registry import register_model
from deeppavlov.core.data.dataset import Dataset

logger = logging.getLogger(__name__)


@register_model('dstc2_dialog_dataset')
class DSTC2Dataset(Dataset):

    @overrides
    def __init__(self, data:Dict[str, List[Tuple[Any, Any]]], *args, **kwargs)\
            -> None:
        def _wrap(turn):
            x = turn[0]['text']
            y = turn[1]['text']
            other = {}
            other['act'] = turn[1]['act']
            if turn[0].get('db_result') is not None:
                other['db_result'] = turn[0]['db_result']
            if turn[0].get('episode_done'):
                other['episode_done'] = True
            return (x, y, other)

        self.train = list(map(_wrap, data.get('train', [])))
        self.valid = list(map(_wrap, data.get('valid', [])))
        self.test = list(map(_wrap, data.get('test', [])))
        self.split(*args, **kwargs)
        self.data = {
            'train': self.train,
            'valid': self.valid,
            'test': self.test,
            'all': self.train + self.test + self.valid
        }

    @overrides
    def batch_generator(self, batch_size:int, data_type:str='train',
                        shuffle:bool=True) -> Generator:
        def _dialog(idx):
            return data[idx['start']: idx['end']]

        data = self.data[data_type]
        dialog_indices = self._dialog_indices(data)
        num_dialogs = len(dialog_indices)
        order = list(range(num_dialogs))
        if shuffle:
            random.shuffle(order)
        for i in range((num_dialogs - 1) // batch_size + 1):
            print("Getting dialogs =", [dialog_indices[o] for o in
                                        order[i*batch_size:(i+1)*batch_size]])
            yield list(itertools.chain.from_iterable(
                _dialog(dialog_indices[o])\
                for o in order[i*batch_size:(i+1)*batch_size]))

    @staticmethod
    def _dialog_indices(data):
        dialog_indices = []
        i, last_idx = 0, 0
        dialog = {}
        for turn in data:
            if turn[2].get('episode_done'):
                if dialog:
                    dialog['end'] = i
                    last_idx = i
                    dialog_indices.append(dialog)
                dialog = {'start': last_idx}
            i += 1
        dialog['end'] = i
        dialog_indices.append(dialog)
        return dialog_indices

    @staticmethod
    def save_vocab(turns, fpath):
        with open(fpath, 'wt') as f:
            words = sorted(set(itertools.chain.from_iterable(
                turn[0].lower().split() for turn in turns
            )))
            f.write(' '.join(words))
