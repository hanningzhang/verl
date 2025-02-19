"""
Preprocess the Numia dataset to parquet format
"""

import os
import datasets

from verl.utils.hdfs_io import copy, makedirs
import argparse

from verl.utils.reward_score.math import remove_boxed, last_boxed_only_string


def extract_solution(solution_str):
    return remove_boxed(last_boxed_only_string(solution_str))

x = datasets.load_dataset("dsrselfcorr/warmup_sft_merged2_clean", split='train')
z = x[0]['conversations'][0]['content']
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--local_dir', default='~/data/numia_math')
    parser.add_argument('--hdfs_dir', default=None)

    args = parser.parse_args()

    data_source = 'dsrselfcorr/rl_prompt2'
    print(f"Loading the {data_source} dataset from huggingface...", flush=True)
    dataset = datasets.load_dataset(data_source, trust_remote_code=True)

    train_dataset = dataset['train']
    test_dataset = dataset['test']

    instruction_following = "Let's think step by step and output the final answer within \\boxed{}."

    # add a row to each data item that represents a unique id
    def make_map_fn(split):

        def process_fn(example, idx):
            question = example.pop('problem')

            question = question + ' ' + instruction_following

            # We set the data_source as MATH so that we can use the reward model designed for MATH dataset
                
            data = {
                "data_source": 'DigitalLearningGmbH/MATH-lighteval',
                "prompt": example['prompt_messages'],
                "ability": "math",
                "reward_model": example['reward_model'],
                "extra_info": {
                    'split': split,
                    'index': idx
                }
            }
            return data

        return process_fn

    train_dataset = train_dataset.map(function=make_map_fn('train'), with_indices=True)
    test_dataset = test_dataset.map(function=make_map_fn('test'), with_indices=True)
    print(train_dataset[0])
    local_dir = args.local_dir
    hdfs_dir = args.hdfs_dir
    train_dataset.to_parquet(os.path.join(local_dir, 'train.parquet'))
    test_dataset.to_parquet(os.path.join(local_dir, 'test.parquet'))

    if hdfs_dir is not None:
        makedirs(hdfs_dir)

        copy(src=local_dir, dst=hdfs_dir)
                                              
