#! /usr/bin/env python3

import argparse
import os
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path
from typing import List

import colorama
import py7zr
import rarfile
from colorama import Fore

colorama.init(autoreset=True)

BINARY_TEXT_ENCODINGS = [
    "UTF-8",
    "EUC-JP",
    "Shift-JIS",
]

LOG_LEVEL = 1
INDENT_LEVEL = 0

found_paths: List[str] = []

def info(msg: str):
    if LOG_LEVEL <= 1:
        print(" " * INDENT_LEVEL + msg)

def warn(msg: str):
    print(Fore.YELLOW + " " * INDENT_LEVEL + msg)

def error(msg: str):
    print(Fore.RED + " " * INDENT_LEVEL + msg)
    sys.exit(1)

def success(msg: str):
    print(Fore.GREEN + " " * INDENT_LEVEL + msg)

def handle_tar(semantic_path: Path, path: Path, string: str):
    info("Extracting tar " + str(path))
    with tempfile.TemporaryDirectory() as tempdir:
        try:
            tarfile.open(path).extractall(tempdir)
        except EOFError:
            warn("Failed to extract tar " + str(path))
            return
        search(semantic_path, Path(tempdir), string)

def handle_zip(semantic_path: Path, path: Path, string: str):
    info("Extracting zip " + str(path))
    
    with tempfile.TemporaryDirectory() as tempdir:
        with zipfile.ZipFile(path, "r") as zip_ref:
            zip_ref.extractall(tempdir)
        search(semantic_path, Path(tempdir), string)

def handle_7z(semantic_path: Path, path: Path, string: str):
    info("Extracting 7z " + str(path))

    with tempfile.TemporaryDirectory() as tempdir:
        try:
            with py7zr.SevenZipFile(path, "r") as archive:
                archive.extractall(tempdir)
        except py7zr.UnsupportedCompressionMethodError:
            warn("Failed to extract 7z " + str(path))
            return
        search(semantic_path, Path(tempdir), string)

def handle_rar(semantic_path: Path, path: Path, string: str):
    info("Extracting rar " + str(path))

    with tempfile.TemporaryDirectory() as tempdir:
        try:
            with rarfile.RarFile(path, "r") as archive:
                archive.extractall(tempdir)
        except rarfile.BadRarFile:
            warn("Failed to extract rar " + str(path))
            return
        search(semantic_path, Path(tempdir), string)

def handle_bin(semantic_path: Path, path: Path, string: str) -> bool:
    with open(path, "rb") as f:
        data = f.read()
        for encoding in BINARY_TEXT_ENCODINGS:
            if bytes(string, encoding) in data:
                success("Found " + string + " in " + str(path) + " with encoding " + encoding)
                return True
    return False

def handle_text(semantic_path: Path, path: Path, string: str):
    try:
        with open(path, "r") as f:
            data = f.read()
            if string in data:
                success("Found " + string + " in " + str(path))
                return True
    except UnicodeDecodeError:
        pass
    return False

def search(semantic_path: Path, path: Path, string: str):
    global INDENT_LEVEL
    info("Entering " + str(semantic_path))
    """Search for a string recursively in a directory of files, extracting archives as needed"""
    
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = Path(root) / file

            if string in str(file_path):
                success("Found " + string + " in filename: " + str(file_path))
                found_paths.append(str(file_path))

            INDENT_LEVEL += 1
            if tarfile.is_tarfile(file_path):
                handle_tar(semantic_path / file, file_path, string)
            elif zipfile.is_zipfile(file_path):
                handle_zip(semantic_path / file, file_path, string)
            elif py7zr.is_7zfile(file_path):
                handle_7z(semantic_path / file, file_path, string)
            elif rarfile.is_rarfile(file_path):
                handle_rar(semantic_path / file, file_path, string)
            else:
                found = handle_bin(semantic_path / file, file_path, string)
                if not found:
                    handle_text(semantic_path / file, file_path, string)
            INDENT_LEVEL -= 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Search for a string recursively in a directory of files, extracting archives as needed')
    parser.add_argument('string', help='String to search for')
    parser.add_argument('path', help='Directory to search', type=Path)
    args = parser.parse_args()

    string = args.string
    path = args.path
    search(path, path, string)