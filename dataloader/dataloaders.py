import torch
from datasets import load_dataset
from torch.utils.data import DataLoader, Dataset

from utils.preprocessing import convert_str_indices_to_token_indices


class ReaderDataset(Dataset):
    """
    Gets training data

    Parameters
    ----------
    qa_dicts : list of dictionaries
        The data structure should look like this:
        [{'answer': 'Project managers, creative types, marketers',
          'context': 'Intake creative project requests tip uses an app ...'
          'mlm': 0.26,  # can be None if not calculated
          'question': 'Who are intake creative project requests useful for?'}, ...]
    fast_tokenizer : A HuggingFace FastTokenizer built upon Rust.
        Used for converting string indices to token indices.
    split : string
        Possible values are 'train' or, if not 'train', then the split
        is considered to be the valid split.
    train_size : float between 0.0 and 1.0
        The size of the train split (validation is the balance remaining).
    """

    def __init__(self,
                 qa_dicts=None,
                 fast_tokenizer=None,
                 split='train',
                 train_size=0.7):
        self.qa_dicts = qa_dicts[:int(len(qa_dicts) * train_size)] if split == 'train' else qa_dicts[int(
            len(qa_dicts) * train_size):]
        self.tokenizer = fast_tokenizer

    def __getitem__(self, item):
        answer = self.qa_dicts[item]['answer']
        context = self.qa_dicts[item]['context'][:2000]  # limiting context for now, but can batch this
        try:
            start_str_index = context.index(answer)
            end_str_index = start_str_index + len(self.qa_dicts[item]['answer'])
        except ValueError:
            start_str_index = 0
            end_str_index = 0
        span_indices = convert_str_indices_to_token_indices(
            context,
            start_str_index,
            end_str_index,
            self.tokenizer)
        targets = span_indices
        return self.qa_dicts[item]['question'], context, torch.tensor(targets)

    def __len__(self):
        return len(self.qa_dicts)


def question_answer_dataloader(qa_dicts, fast_tokenizer, batch_size=1, split='train', train_size=0.7, **kwargs):
    return DataLoader(ReaderDataset(
        qa_dicts, fast_tokenizer=fast_tokenizer, split=split, train_size=train_size), batch_size=batch_size,
        **kwargs)


def question_generator_dataloader(split='train', batch_size=8):
    dataset = load_dataset('squad', split=split)
    return DataLoader(dataset, batch_size=batch_size, shuffle=True)
