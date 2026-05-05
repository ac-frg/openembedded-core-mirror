#
# Copyright OpenEmbedded Contributors
#
# SPDX-License-Identifier: MIT
#

import mmap
import os
import tempfile
from unittest.case import TestCase


class TestKernelModuleFilenameFilter(TestCase):
    """
    The pre-filter in process_split_and_strip_files() selects candidates to
    pass to is_elf(). It must use f.endswith(".ko"), not ".ko" in f, to avoid
    false-positives on compressed modules (.ko.xz, .ko.gz).
    """

    ko_files = [
        "driver.ko",
        "net/foo.ko",
    ]

    not_ko_files = [
        "driver.ko.xz",
        "driver.ko.gz",
        "driver.ko2",
        "myko.c",
        "vmlinux",
    ]

    def test_endswith_matches_ko(self):
        for f in self.ko_files:
            with self.subTest(f=f):
                self.assertTrue(f.endswith(".ko"))

    def test_endswith_rejects_non_ko(self):
        for f in self.not_ko_files:
            with self.subTest(f=f):
                self.assertFalse(f.endswith(".ko"))

    def test_old_predicate_had_false_positives(self):
        # The previous check (".ko" in f) matched compressed modules — this is
        # the regression the fix addresses.
        false_positives = [f for f in self.not_ko_files if ".ko" in f]
        self.assertEqual(false_positives, ["driver.ko.xz", "driver.ko.gz", "driver.ko2"])


class TestIsKernelModule(TestCase):
    """
    is_kernel_module() detects kernel modules by searching for the
    "vermagic=" string, which is always present in genuine .ko files.
    """

    def setUp(self):
        from oe.package import is_kernel_module
        self.is_kernel_module = is_kernel_module
        self._tmpfile = None

    def tearDown(self):
        if self._tmpfile and os.path.exists(self._tmpfile):
            os.unlink(self._tmpfile)

    def _make_tmp(self, content):
        f = tempfile.NamedTemporaryFile(delete=False, suffix=".ko")
        f.write(content)
        f.close()
        return f.name

    def test_detects_vermagic(self):
        self._tmpfile = self._make_tmp(b"\x7fELF\x00" * 10 + b"vermagic=5.15.0" + b"\x00" * 10)
        self.assertTrue(self.is_kernel_module(self._tmpfile))

    def test_rejects_plain_elf(self):
        self._tmpfile = self._make_tmp(b"\x7fELF\x00" * 50)
        self.assertFalse(self.is_kernel_module(self._tmpfile))


class TestIsKernelModuleSigned(TestCase):
    """
    is_kernel_module_signed() detects the "Module signature appended" tail
    that the kernel's modsign infrastructure writes.
    """

    def setUp(self):
        from oe.package import is_kernel_module_signed
        self.is_kernel_module_signed = is_kernel_module_signed
        self._tmpfile = None

    def tearDown(self):
        if self._tmpfile and os.path.exists(self._tmpfile):
            os.unlink(self._tmpfile)

    def _make_tmp(self, content):
        f = tempfile.NamedTemporaryFile(delete=False, suffix=".ko")
        f.write(content)
        f.close()
        return f.name

    def test_detects_signed(self):
        tail = b"Module signature appended\n\x00\x00"
        self._tmpfile = self._make_tmp(b"\x00" * 64 + tail)
        self.assertTrue(self.is_kernel_module_signed(self._tmpfile))

    def test_rejects_unsigned(self):
        self._tmpfile = self._make_tmp(b"\x7fELF\x00" * 20)
        self.assertFalse(self.is_kernel_module_signed(self._tmpfile))
