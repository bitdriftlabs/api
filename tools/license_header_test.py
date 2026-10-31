# api - bitdrift's client/server API definitions
# Copyright Bitdrift, Inc. All rights reserved.
#
# Use of this source code and APIs are governed by a source available license that can be found in
# the LICENSE file or at:
# https://polyformproject.org/licenses/strict/1.0.0

import importlib.util
import pathlib
import subprocess
import tempfile
import unittest


SCRIPT = pathlib.Path(__file__).with_name('license_header.py').resolve()
REPO = SCRIPT.parent.parent
SPEC = importlib.util.spec_from_file_location('license_header', SCRIPT)
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


class LicenseHeaderTest(unittest.TestCase):
    def setUp(self):
        scratch = REPO / '.tmp'
        scratch.mkdir(exist_ok=True)
        directory = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(directory.cleanup)
        self.root = pathlib.Path(directory.name)
        subprocess.run(['git', 'init', '--quiet', str(self.root)], check=True)
        (self.root / 'LICENSE').write_bytes((REPO / 'LICENSE').read_bytes())

    def run_checker(self, *args):
        return subprocess.run(
            ['python3', str(SCRIPT), *args], cwd=self.root, capture_output=True, text=True)

    def test_check_reports_all_missing_headers_without_modifying_files(self):
        for name in ('first.proto', 'second file.fbs'):
            (self.root / name).write_text('body\n')
        result = self.run_checker('--check')
        self.assertEqual(result.returncode, 1)
        for name in ('first.proto', 'second file.fbs'):
            self.assertIn(name, result.stderr)
            self.assertEqual((self.root / name).read_text(), 'body\n')

    def test_canonical_header_normalization_preserves_notices_and_schema_bodies(self):
        notice = '// Copyright upstream. Apache License 2.0.\n'
        notice = '\n'.join(CHECKER.HEADER.splitlines()[:2]) + '\n\n' + notice
        for extension, body in (
            ('.proto', 'syntax = "proto3";\nmessage Test {}\n'),
            ('.fbs', 'namespace test;\ntable Test {}\n'),
        ):
            path = self.root / ('source' + extension)
            original = CHECKER.HEADER + '\n' + CHECKER.HEADER + '\n' + notice + body
            path.write_text(original)
            self.assertEqual(self.run_checker('--check').returncode, 1)
            self.assertEqual(path.read_text(), original)
            self.assertEqual(self.run_checker().returncode, 0)
            expected = CHECKER.HEADER + '\n' + notice + body
            self.assertEqual(path.read_text(), expected)
            self.assertEqual(self.run_checker().returncode, 0)
            self.assertEqual(path.read_text(), expected)
            self.assertEqual(self.run_checker('--check').returncode, 0)
            path.unlink()

    def test_noncanonical_headers_are_rejected_without_writes(self):
        incorrect = CHECKER.HEADER.replace(
            CHECKER.STRICT_URL, 'https://example.invalid/obsolete-license')
        for extension in ('.proto', '.fbs'):
            path = self.root / ('source' + extension)
            for original in (
                incorrect + '\nbody\n',
                CHECKER.HEADER + '\n' + incorrect + '\nbody\n',
            ):
                for args in ((), ('--check',)):
                    with self.subTest(extension=extension, args=args, header=original):
                        path.write_text(original)
                        result = self.run_checker(*args, str(path))
                        self.assertEqual(result.returncode, 1)
                        self.assertIn('Unrecognized license header', result.stderr)
                        self.assertEqual(path.read_text(), original)
            path.unlink()

    def test_generated_sync_header_without_separator_is_normalized(self):
        path = self.root / 'public.proto'
        path.write_text(CHECKER.HEADER + 'syntax = "proto3";\n')
        self.assertEqual(self.run_checker().returncode, 0)
        self.assertEqual(path.read_text(), CHECKER.HEADER + '\nsyntax = "proto3";\n')
        self.assertEqual(self.run_checker('--check').returncode, 0)

    def test_relative_absolute_and_uncommitted_paths(self):
        path = self.root / 'new file.proto'
        path.write_text('body\n')
        self.assertEqual(self.run_checker(str(path)).returncode, 0)
        for name in (str(path), path.name, './' + path.name):
            result = self.run_checker('--check', name)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_vendored_and_ignored_files_are_untouched(self):
        (self.root / '.gitignore').write_text('build/\n')
        for name in (
            'build/output.proto',
            'thirdparty/upstream.proto',
            'protoc-gen-validate/validate/validate.proto',
        ):
            path = self.root / name
            path.parent.mkdir(parents=True)
            path.write_text('upstream\n')
        self.assertEqual(self.run_checker().returncode, 0)
        for name in (
            'build/output.proto',
            'thirdparty/upstream.proto',
            'protoc-gen-validate/validate/validate.proto',
        ):
            path = self.root / name
            self.assertEqual(path.read_text(), 'upstream\n')
            if not name.startswith('build/'):
                self.assertEqual(self.run_checker('--check', str(path)).returncode, 0)

    def test_directory_exclusions_do_not_match_first_party_prefixes(self):
        for name in ('thirdparty_extension/file.proto', '.github/fixture.fbs'):
            path = self.root / name
            path.parent.mkdir(parents=True)
            path.write_text('body\n')
        self.assertEqual(self.run_checker('--check').returncode, 1)
        self.assertEqual(self.run_checker().returncode, 0)
        self.assertEqual(self.run_checker('--check').returncode, 0)

    def test_license_integrity_and_missing_files_fail(self):
        license_file = self.root / 'LICENSE'
        license_file.write_text(license_file.read_text() + '\nAdditional terms\n')
        self.assertEqual(self.run_checker('--check').returncode, 1)
        license_file.unlink()
        self.assertEqual(self.run_checker('--check').returncode, 1)

    def test_missing_explicit_file_fails(self):
        result = self.run_checker('--check', 'missing.proto')
        self.assertEqual(result.returncode, 1)
        self.assertIn('missing.proto', result.stderr)

    def test_shell_check_ignores_unrelated_dirt_and_never_fixes_headers(self):
        tools = self.root / 'tools'
        tools.mkdir()
        (tools / 'license_header.py').write_bytes(SCRIPT.read_bytes())
        (self.root / 'unrelated.md').write_text('uncommitted\n')
        source = self.root / 'source.proto'
        source.write_text(CHECKER.HEADER + '\nbody\n')
        command = ['bash', str(REPO / 'tools/check_license.sh'), 'source.proto']
        result = subprocess.run(command, cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        source.write_text('body\n')
        result = subprocess.run(command, cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(source.read_text(), 'body\n')


if __name__ == '__main__':
    unittest.main()
