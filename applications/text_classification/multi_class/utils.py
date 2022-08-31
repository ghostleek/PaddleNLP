# Copyright (c) 2022 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy as np

import paddle
import paddle.nn.functional as F
from paddlenlp.utils.log import logger


@paddle.no_grad()
def evaluate(model, criterion, metric, data_loader):
    """
    Given a dataset, it evaluates model and computes the metric.
    Args:
        model(obj:`paddle.nn.Layer`): A model to classify texts.
        criterion(obj:`paddle.nn.Layer`): It can compute the loss.
        metric(obj:`paddle.metric.Metric`): The evaluation metric.
        data_loader(obj:`paddle.io.DataLoader`): The dataset loader which generates batches.
    """

    model.eval()
    metric.reset()
    losses = []
    for batch in data_loader:
        input_ids, token_type_ids, labels = batch['input_ids'], batch[
            'token_type_ids'], batch['labels']
        logits = model(input_ids, token_type_ids)
        loss = criterion(logits, labels)
        losses.append(loss.numpy())
        correct = metric.compute(logits, labels)
        metric.update(correct)

    acc = metric.accumulate()
    logger.info("eval loss: %.5f, acc: %.5f" % (np.mean(losses), acc))
    model.train()
    metric.reset()

    return acc


def preprocess_function(examples, tokenizer, max_seq_length, is_test=False):
    """
    Builds model inputs from a sequence for sequence classification tasks
    by concatenating and adding special tokens.
        
    Args:
        examples(obj:`list[str]`): List of input data, containing text and label if it have label.
        tokenizer(obj:`PretrainedTokenizer`): This tokenizer inherits from :class:`~paddlenlp.transformers.PretrainedTokenizer` 
            which contains most of the methods. Users should refer to the superclass for more information regarding methods.
        max_seq_length(obj:`int`): The maximum total input sequence length after tokenization. 
            Sequences longer than this will be truncated, sequences shorter will be padded.
        label_nums(obj:`int`): The number of the labels.
    Returns:
        result(obj:`dict`): The preprocessed data including input_ids, token_type_ids, labels.
    """
    result = tokenizer(text=examples["text"], max_seq_len=max_seq_length)
    if not is_test:
        result["labels"] = np.array([examples['label']], dtype='int64')
    return result


def read_local_dataset(path, label_list):
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            sentence, label = line.strip().split('\t')
            yield {'text': sentence, 'label': label_list[label]}