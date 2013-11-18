from argparse import RawTextHelpFormatter, ArgumentParser
import logging
import os
import shutil
import tempfile
from oncotator.utils.install.DatasourceInstallUtils import DatasourceInstallUtils
from oncotator.utils.install.GenomeBuildFactory import GenomeBuildFactory
from oncotator.utils.version import VERSION


def setup_logging():
    # Add a console logger to the root logger, which means that all loggers generated will have the console dump.
    #    Output on the console will be the same as what is in the log file.
    logging_format = '%(asctime)s %(levelname)s [%(name)s:%(lineno)d] %(message)s'
    logging.basicConfig(level=logging.INFO, format=logging_format)
    logging.getLogger(__name__).info("Version: " + VERSION)


def parseOptions():

    epilog = """    This utility can require a lot of RAM (~4GB for gencode.v18).
    Creation of a gencode datasource can require as much as two hours.
    """
    desc = "Create a gencode/ensembl based datasource."
    parser = ArgumentParser(description=desc, formatter_class=RawTextHelpFormatter, epilog=epilog)
    parser.add_argument("gtf_files", type=str, help="Location of the gtf files.  Multiple files can be specified as a comma separated list (e.g. file1,file2) without spaces ")
    parser.add_argument("fasta_files", type=str, help="Location of the fasta file (cDNA) associated with the gtf files.  Multiple files can be specified as a comma separated list (e.g. file1,file2) without spaces")
    parser.add_argument("output_dir", type=str, help="Datasource output location")
    parser.add_argument("genome_build", type=str, help="Genome build -- this must be specified correctly by the user.  For example, hg19.")

    # Process arguments
    args = parser.parse_args()

    logger = logging.getLogger(__name__)
    logger.info("Args: " + str(args))

    return args

def main():
    setup_logging()
    args = parseOptions()
    gtf_files = args.gtf_files.split(",")
    fasta_files = args.fasta_files.split(",")
    output_dir = args.output_dir
    genome_build = args.genome_build

    # create temp dir
    tmpDir = tempfile.mkdtemp(prefix="onco_ensembl_ds_")
    try:
        logging.getLogger(__name__).info("Creating tmp dir (" + tmpDir + ") ....")
        ds_build_dir = tmpDir + "/" + genome_build + "/"
        os.mkdir(ds_build_dir)

        logging.getLogger(__name__).info("Starting index construction (temp location: " + ds_build_dir + ") ...")
        factory = GenomeBuildFactory()
        factory.construct_ensembl_indices(gtf_files, fasta_files, ds_build_dir + os.path.basename(gtf_files[0]))

        logging.getLogger(__name__).info("Creating datasource md5...")
        DatasourceInstallUtils.create_datasource_md5_file(ds_build_dir)

        logging.getLogger(__name__).info("Copying created datasource from temp directory to final location (" + output_dir + ")...")
        shutil.copytree(symlinks=True, src=tmpDir, dst=output_dir)

    except Exception as e:
        import traceback
        logging.getLogger(__name__).fatal((e.__repr__()) + " " + traceback.format_exc())
        logging.getLogger(__name__).info(""""If you are getting and error such as:  KeyError: 'ENST00000474204.1'), then you may be out of disk space in /tmp/.""")

    # Remove the tempdir
    logging.getLogger(__name__).info("Done...")
    logging.getLogger(__name__).info("Removing ..." + tmpDir + '/')
    shutil.rmtree(tmpDir)

if __name__ == '__main__':
    main()