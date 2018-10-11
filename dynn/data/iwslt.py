#!/usr/bin/env python3
"""
IWSLT
^^^^^

Various functions for accessing the IWSLT translation datasets
"""
import os
import tarfile
import re

from .data_util import download_if_not_there

iwslt_url = "https://wit3.fbk.eu/archive"
supported = {
    "2016.de-en": {
        "train": "train.tags.de-en",
        "dev": "IWSLT16.TED.tst2013.de-en",
        "test": "IWSLT16.TED.tst2014.de-en"
    },
    "2016.fr-en": {
        "train": "train.tags.fr-en",
        "dev": "IWSLT16.TED.tst2013.fr-en",
        "test": "IWSLT16.TED.tst2014.fr-en"
    },
}
supported_string = ", ".join(supported)


# Regex for filtering metadata
is_meta = re.compile(r"^<.*")
not_seg = re.compile(r"^(?!<seg.).*")
eval_segment = re.compile(r"^<seg[^>]*>(.*)</seg>")


def local_dir(year, langpair):
    return f"iwslt{year}.{langpair}"


def download_iwslt(path=".", year="2016", langpair="de-en", force=False):
    """Downloads the IWSLT from "https://wit3.fbk.eu/archive/"

    Args:
        path (str, optional): Local folder (defaults to ".")
        force (bool, optional): Force the redownload even if the files are
            already at ``path``
    """
    src, tgt = langpair.split("-")
    langpair_url = f"{iwslt_url}/{year}-01//texts/{src}/{tgt}/"
    langpair_file = f"{langpair}.tgz"
    local_file = f"iwslt{year}.{langpair}.tgz"
    downloaded = download_if_not_there(
        langpair_file,
        langpair_url,
        path,
        force=force,
        local_file=local_file
    )
    # Extract
    if downloaded:
        abs_filename = os.path.join(os.path.abspath(path), local_file)
        # Create target dir
        directory = local_dir(year, langpair)
        if not os.path.isdir(directory):
            os.mkdir(directory)
        # Extract
        with tarfile.open(abs_filename) as tar:
            tar.extractall(directory)


def read_iwslt(split, path, year="2016", langpair="de-en", eos=None):
    """Iterates over the IWSLT dataset

    Example:

    .. code-block:: python

        for src, tgt in read_iwslt("train", "/path/to/iwslt"):
            train(src, tgt)

    Args:
        split (str): Either ``"train"``, ``"dev"`` or ``"test"``
        path (str): Path to the folder containing the ``.tgz`` file
        eos (str, optional): Optionally append an end of sentence token to
            each line


    Returns:
        tuple: tree, label
    """
    if not (split is "test" or split is "dev" or split is "train"):
        raise ValueError("split must be \"train\", \"dev\" or \"test\"")
    is_train = split is "train"
    # Languages
    src, tgt = langpair.split("-")
    # Local dir
    directory = local_dir(year, langpair)
    root_path = os.path.join(os.path.abspath(path), directory)
    # Retrieve source/target file
    prefix = supported[f"{year}.{langpair}"][split]
    src_file = os.path.join(root_path, langpair, f"{prefix}.{src}")
    tgt_file = os.path.join(root_path, langpair, f"{prefix}.{tgt}")
    if not is_train:
        src_file = f"{src_file}.xml"
        tgt_file = f"{tgt_file}.xml"
    src_obj = open(src_file, encoding="utf-8")
    tgt_obj = open(tgt_file, encoding="utf-8")
    # Read lines
    for src_l, tgt_l in zip(src_obj, tgt_obj):
        # src_l, tgt_l = src_bytes.decode(), tgt_bytes.decode()
        # Skip metadata
        if is_train and is_meta.match(src_l) and is_meta.match(tgt_l):
            continue
        if not is_train:
            src_seg = eval_segment.match(src_l)
            tgt_seg = eval_segment.match(tgt_l)
            if src_seg is None or tgt_seg is None:
                continue
            # Strip segments
            src_l = src_seg.group(1)
            tgt_l = tgt_seg.group(1)
        # Split
        src_l = src_l.strip().split()
        tgt_l = tgt_l.strip().split()
        # Append eos maybe
        if eos is not None:
            src_l.append(eos)
            tgt_l.append(eos)
        # Return
        yield src_l, tgt_l

    src_obj.close()
    tgt_obj.close()


def load_iwslt(path, year="2016", langpair="de-en", eos=None):
    """Loads the IWSLT dataset

    Returns the train, dev and test set, each as lists of source and target
    sentences.

    Args:
        path (str): Path to the folder containing the ``.tgz`` file
        eos (str, optional): Optionally append an end of sentence token to
            each line


    Returns:
        tuple: train, dev and test sets
    """
    if f"{year}.{langpair}" not in supported:
        raise ValueError(
            f"{year}.{langpair} not supported. "
            f"Supported datasets are {supported_string}"
        )
    splits = []
    for split in ["train", "dev", "test"]:
        data = list(read_iwslt(
            split,
            path,
            year=year,
            langpair=langpair,
            eos=eos
        ))
        src_data = [src for src, _ in data]
        tgt_data = [tgt for _, tgt in data]
        splits.append((src_data, tgt_data))

    return tuple(splits)