# Copyright 2018 The Google AI Language Team Authors and
# The HuggingFace Inc. team.
# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
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
from logging import config
from nemo.collections.nlp.modules.common.decoder_module import DecoderModule
from nemo.collections.nlp.modules.common.transformer.transformer_utils import get_nemo_transformer_model
from nemo.collections.nlp.modules.common.encoder_module import EncoderModule
import os
from typing import List, Optional, Union

from nemo.collections.nlp.modules.common.bert_module import BertModule
from nemo.collections.nlp.modules.common.huggingface.huggingface_utils import (
    get_huggingface_lm_model,
    get_huggingface_pretrained_lm_models_list,
)
from nemo.collections.nlp.modules.common.megatron.megatron_utils import (
    get_megatron_lm_model,
    get_megatron_lm_models_list,
)
from nemo.utils import logging

__all__ = ['get_pretrained_lm_models_list', 'get_lm_model']


def get_pretrained_lm_models_list(include_external: bool = False) -> List[str]:
    """
    Returns the list of supported pretrained model names

    Args:
        include_external if true includes all HuggingFace model names, not only those supported language models in NeMo.

    """
    return get_megatron_lm_models_list() + get_huggingface_pretrained_lm_models_list(include_external=include_external)


def get_lm_model(
    pretrained_model_name: str,
    config_dict: Optional[dict] = None,
    config_file: Optional[str] = None,
    checkpoint_file: Optional[str] = None,
) -> BertModule:
    """
    Helper function to instantiate a language model encoder, either from scratch or a pretrained model.
    If only pretrained_model_name are passed, a pretrained model is returned.
    If a configuration is passed, whether as a file or dictionary, the model is initialized with random weights.

    Args:
        pretrained_model_name: pretrained model name, for example, bert-base-uncased or megatron-bert-cased.
            See get_pretrained_lm_models_list() for full list.
        config_dict: path to the model configuration dictionary
        config_file: path to the model configuration file
        checkpoint_file: path to the pretrained model checkpoint

    Returns:
        Pretrained BertModule
    """

    # check valid model type
    if not pretrained_model_name or pretrained_model_name not in get_pretrained_lm_models_list(include_external=False):
        logging.warning(
            f'{pretrained_model_name} is not in get_pretrained_lm_models_list(include_external=False), '
            f'will be using AutoModel from HuggingFace.'
        )

    # warning when user passes both configuration dict and file
    if config_dict and config_file:
        logging.warning(
            f"Both config_dict and config_file were found, defaulting to use config_file: {config_file} will be used."
        )

    if "megatron" in pretrained_model_name:
        model, checkpoint_file = get_megatron_lm_model(
            config_dict=config_dict,
            config_file=config_file,
            pretrained_model_name=pretrained_model_name,
            checkpoint_file=checkpoint_file,
        )
    else:
        model = get_huggingface_lm_model(
            config_dict=config_dict, config_file=config_file, pretrained_model_name=pretrained_model_name,
        )

    if checkpoint_file and os.path.exists(checkpoint_file):
        model.restore_weights(restore_path=checkpoint_file)

    return model


def get_transformer(
    library: str = 'nemo',
    model_name: Optional[str] = None,
    pretrained: bool = False,
    config_dict: Optional[dict] = None,
    checkpoint_file: Optional[str] = None,
    encoder: bool = True,
) -> Union[EncoderModule, DecoderModule]:

    module = None

    if library == 'nemo':
        if model_name is not None:
            logging.error(f'NeMo transformers cannot be loaded from NGC yet.')

        module = get_nemo_transformer_model(model_name, config_dict, encoder)

        if checkpoint_file is not None:
            if os.path.isfile(checkpoint_file):
                logging.info(f'Checkpoint found at {checkpoint_file} will be used to restore weights.')
                logging.error(f'Loading transformer weights from checkpoint file has not been implemented yet.')
            else:
                logging.error(f'Checkpoint not found at {checkpoint_file}.')

    return module
