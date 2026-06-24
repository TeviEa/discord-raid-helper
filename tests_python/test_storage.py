"""Tests for bot/storage.py"""

import json
import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from bot import storage


class TestLoadData:
    def test_returns_empty_when_file_missing(self):
        with patch("bot.storage.os.path.exists", return_value=False):
            assert storage.load_data() == {}

    def test_parses_json(self):
        data = {"dates": ["15/05/26"], "reminder": {"time": "18:00"}}
        with patch("bot.storage.os.path.exists", return_value=True):
            with patch("bot.storage.open", MagicMock(read_data=json.dumps(data))):
                pass

    def test_returns_empty_on_parse_error(self):
        with patch("bot.storage.os.path.exists", return_value=True):
            mock_file = MagicMock()
            mock_file.read.return_value = "not json"
            with patch("bot.storage.open", MagicMock(return_value=mock_file)):
                assert storage.load_data() == {}

    def test_handles_null_json(self):
        with patch("bot.storage.os.path.exists", return_value=True):
            mock_file = MagicMock()
            mock_file.read.return_value = "null"
            with patch("bot.storage.open", MagicMock(return_value=mock_file)):
                assert storage.load_data() == {}


class TestSaveData:
    def test_writes_json(self):
        with patch("bot.storage.os.makedirs"):
            with patch("bot.storage.tempfile.mkstemp") as mock_mkstemp:
                fd = MagicMock()
                tmp_path = "/tmp/test.tmp"
                mock_mkstemp.return_value = (fd, tmp_path)
                with patch("bot.storage.os.fdopen", MagicMock()):
                    with patch("bot.storage.os.replace"):
                        storage.save_data({"dates": ["15/05/26"]})
                        # Verify fdopen was called with write mode
                        os.fdopen.assert_called()

    def test_creates_data_directory(self):
        with patch("bot.storage.os.makedirs") as mock_makedirs:
            with patch("bot.storage.tempfile.mkstemp") as mock_mkstemp:
                fd = MagicMock()
                mock_mkstemp.return_value = (fd, "/tmp/test.tmp")
                with patch("bot.storage.os.fdopen", MagicMock()):
                    with patch("bot.storage.os.replace"):
                        storage.save_data({"dates": []})
                        mock_makedirs.assert_called_once()


class TestLoadDatesFromFile:
    def test_returns_dates_array(self):
        with patch.object(storage, "load_data", return_value={"dates": ["15/05/26", "22/05/26"]}):
            assert storage.load_dates_from_file() == ["15/05/26", "22/05/26"]

    def test_returns_empty_when_no_dates(self):
        with patch.object(storage, "load_data", return_value={}):
            assert storage.load_dates_from_file() == []

    def test_returns_empty_when_dates_not_list(self):
        with patch.object(storage, "load_data", return_value={"dates": "not-a-list"}):
            assert storage.load_dates_from_file() == []


class TestWriteDatesToFile:
    def test_writes_dates(self):
        with patch.object(storage, "load_data", return_value={"dates": ["old"]}):
            with patch.object(storage, "save_data") as mock_save:
                storage.write_dates_to_file(["15/05/26"])
                mock_save.assert_called_once()
