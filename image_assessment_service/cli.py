import structlog

from image_assessment_service.config import load_config, get_config


def cli_runner():
    args = parse_args()
    logger = structlog.get_logger()
    logger.info(f'Use config: {args.config_path}')

    load_config(args.config_path)
    config = get_config()
    logger.info("Config loaded")

    from image_assessment_service.app import build_app, run_app
    app = build_app()
    run_app(app, config.application.host, config.application.port)

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
    return parser.parse_args()


if __name__ == '__main__':
    cli_runner()

