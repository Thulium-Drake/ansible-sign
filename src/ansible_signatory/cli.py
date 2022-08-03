import argparse
import logging
import os
import sys

from ansible_signatory import __version__
from ansible_signatory.checksum import ChecksumFile, ChecksumMismatch
from ansible_signatory.checksum.differ import *

__author__ = "Rick Elrod"
__copyright__ = "(c) 2022 Red Hat, Inc."
__license__ = "MIT"

_logger = logging.getLogger(__name__)


DIFFER_MAP = {
    'git': GitChecksumFileExistenceDiffer,
    'directory': DirectoryChecksumFileExistenceDiffer,
}

def parse_args(args):
    """Parse command line parameters

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--help"]``).

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """

    parser = argparse.ArgumentParser(description="Signing and validation for Ansible content")
    parser.add_argument(
        "--version",
        action="version",
        version="ansible-signatory {ver}".format(ver=__version__),
    )
    parser.add_argument(
        "--debug",
        help="Print a bunch of debug info",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG
    )

    commands = parser.add_subparsers(required=True, dest="command")

    # command: validate-checksum
    cmd_validate_checksum = commands.add_parser(
        "validate-checksum",
        help="Perform checksum file validation (NOT including signature signing)",
    )
    cmd_validate_checksum.set_defaults(func=validate_checksum)
    cmd_validate_checksum.add_argument(
        "--checksum-file",
        help="The checksum file to use",
        required=False,
        metavar="CHECKSUM_FILE",
        dest="checksum_file",
        default="sha256sum.txt",
    )
    cmd_validate_checksum.add_argument(
        "--scm",
        help="The source code management system (if any) storing the files. Used for skipping files that the SCM ignores.",
        required=False,
        metavar="SCM",
        dest="scm",
        default="auto",
        choices=list(DIFFER_MAP.keys()) + ['auto'],
    )
    cmd_validate_checksum.add_argument(
        "--ignore-file-list-differences",
        help="Do not fail validation even if files have been added or removed, and the current manifest is out of date. Only check those files listed in the manifest.",
        default=False,
        action="store_true",
        dest="ignore_file_list_differences",
    )
    cmd_validate_checksum.add_argument(
        "project_root",
        help="The directory containing the files being validated and verified",
        metavar="PROJECT_ROOT",
    )

    # command: validate-gpg-signature
    cmd_validate_gpg_signature = commands.add_parser(
        "validate-gpg-signature",
        help="Perform GPG signature validation on the checksum manifest (NOT including checksum verification)",
    )
    cmd_validate_gpg_signature.set_defaults(func=validate_gpg_signature)
    cmd_validate_gpg_signature.add_argument(
        "--signature-file",
        help="An optional detached signature file",
        required=False,
        metavar="SIGNATURE_FILE",
        dest="signature_file",
        default="sha256sum.txt.sig",
    )
    cmd_validate_gpg_signature.add_argument(
        "checksum_file",
        help="The checksum file that was signed",
        metavar="CHECKSUM_FILE",
        default="sha256sum.txt",
    )

    # command: checksum-manifest
    cmd_checksum_manifest = commands.add_parser(
        "checksum-manifest",
        help="Generate a checksum manifest file for the project",
    )
    cmd_checksum_manifest.set_defaults(func=checksum_manifest)
    cmd_checksum_manifest.add_argument(
        "--algorithm",
        help="Which checksum hashing algorithm to use",
        required=False,
        choices=ChecksumFile.MODES,
        metavar="ALGORITHM",
        dest="algorithm",
        default="sha256",
    )
    cmd_checksum_manifest.add_argument(
        "--output",
        help="An optional filename to which to write the resulting manifest",
        required=False,
        metavar="OUTPUT",
        dest="output",
        default="-",
    )
    cmd_checksum_manifest.add_argument(
        "--scm",
        help="The source code management system (if any) storing the files. Used for skipping files that the SCM ignores.",
        required=False,
        metavar="SCM",
        dest="scm",
        default="auto",
        choices=list(DIFFER_MAP.keys()) + ['auto'],
    )
    return parser.parse_args(args)


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(
        level=loglevel, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S"
    )

def get_differ(scm, project_root):
    if scm == 'auto':
        return determine_differ_from_auto(project_root)

    # This key is guaranteed to exist by the arg choices limit
    return DIFFER_MAP[scm]

def determine_differ_from_auto(project_root):
    """
    Attempt to determine the SCM a project is using, if any.
    """

    root_files = os.listdir(project_root)
    if '.git' in root_files:
        return GitChecksumFileExistenceDiffer
    #if '.svn' in root_files:
    #    return SubversionChecksumFileExistenceDiffer
    return DirectoryChecksumFileExistenceDiffer

def validate_checksum(args):
    differ = get_differ(args.scm, args.project_root)
    checksum = ChecksumFile(args.project_root, differ=differ)

    if not os.path.exists(args.checksum_file):
        print(f"Checksum file does not exist: {args.checksum_file}")
        return 1

    checksum_file_contents = open(args.checksum_file, 'r').read()
    manifest = checksum.parse(checksum_file_contents)

    try:
        checksum.verify(manifest, diff=not args.ignore_file_list_differences)
    except ChecksumMismatch as e:
        print("Checksum validation FAILED!")
        print(str(e))
        return 2

    print("Checksum validation SUCCEEDED!")

def validate_gpg_signature(args):
    print('hi')

def checksum_manifest(args):
    print('hi')

def main(args):
    """Wrapper allowing :func:`fib` to be called with string arguments in a CLI fashion

    Instead of returning the value from :func:`fib`, it prints the result to the
    ``stdout`` in a nicely formatted message.

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--verbose", "42"]``).
    """
    args = parse_args(args)
    setup_logging(args.loglevel)
    _logger.debug("Starting crazy calculations...")
    exitcode = args.func(args)
    _logger.info("Script ends here")
    return exitcode


def run():
    """Calls :func:`main` passing the CLI arguments extracted from :obj:`sys.argv`

    This function can be used as entry point to create console scripts with setuptools.
    """
    return main(sys.argv[1:])


if __name__ == "__main__":
    run()
