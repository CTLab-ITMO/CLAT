import structlog
from dotenv import load_dotenv

from image_assessment_service.config import load_config


def cli_runner():
    args = parse_args()
    logger = structlog.get_logger()
    logger.info(f'Use config: {args.config_path}')

    load_dotenv()
    load_config(args.config_path)

    from image_assessment_service.assessment.app import AssessmentApp

    service_codes = args.services.split(",") if args.services else None
    AssessmentApp(service_codes=service_codes).run()


def parse_args():
    import argparse
    import pathlib

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--config',
        dest='config_path',
        help='Path to configuration file',
        type=pathlib.Path
    )
    parser.add_argument(
        '--services',
        dest='services',
        help='Comma-separated list of service/feature codes to run (e.g. tech,filter). By default runs all enabled',
        default=None,
    )
    return parser.parse_args()


if __name__ == '__main__':
    cli_runner()